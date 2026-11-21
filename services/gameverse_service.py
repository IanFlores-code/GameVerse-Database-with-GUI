from db.db_manager import DatabaseManager


class GameVerseService:
    @staticmethod
    def get_wallet_summary(wallet_id):
        query = "SELECT walletid, balance, wallettype FROM wallets WHERE walletid = %s;"
        success, result = DatabaseManager.execute_query(query, (wallet_id,), fetch=True)
        if success and result:
            return True, result[0]
        return False, "Wallet not found or query failed"

    @staticmethod
    def check_sufficient_balance(wallet_id, required_amount):
        query = "SELECT balance FROM wallets WHERE walletid = %s;"
        success, result = DatabaseManager.execute_query(query, (wallet_id,), fetch=True)
        if success and result:
            balance = result[0][0]
            if balance >= required_amount:
                return True, True
            return True, False
        return False, "Wallet not found"

    @staticmethod
    def get_low_balance_alerts(threshold):
        query = "SELECT walletid, balance FROM wallets WHERE balance < %s;"
        success, result = DatabaseManager.execute_query(query, (threshold,), fetch=True)
        if success:
            return True, result
        return False, "Query failed"

    @staticmethod
    def get_player_profile(player_id):
        query = (
            "SELECT playerid, firstname, lastname, email, phone, isactive, "
            "dateofbirth, registrationdate FROM players WHERE playerid = %s;"
        )
        success, result = DatabaseManager.execute_query(query, (player_id,), fetch=True)
        if success and result:
            return True, result[0]
        return False, "Player not found or query failed"

    @staticmethod
    def get_wallet_transactions(wallet_id):
        query = """
            SELECT transactionid, transactiondate, amount, transactiontype, recipient, paymentmethod 
            FROM gametransactions 
            WHERE walletid = %s 
            ORDER BY transactiondate DESC;
        """
        success, result = DatabaseManager.execute_query(query, (wallet_id,), fetch=True)
        if success:
            return True, result
        return False, "Query failed"

    @staticmethod
    def record_transaction(wallet_id, amount, transaction_type, recipient=None, payment_method=None):
        query = """
            INSERT INTO gametransactions (transactionid, walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
            VALUES (
                (SELECT COALESCE(MAX(transactionid), 8000) + 1 FROM gametransactions),
                %s, CURRENT_DATE, %s, %s, %s, %s
            )
            RETURNING transactionid;
        """
        success, result = DatabaseManager.execute_query(query, (wallet_id, amount, transaction_type, recipient,
                                                                payment_method), fetch=True)
        if success and result:
            return True, result[0][0]
        return False, "Failed to record transaction"

    @staticmethod
    def get_gaming_hubs():
        query = "SELECT hubid, hubname, location, isactive FROM gaminghubs;"
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, "Failed to fetch gaming hubs"

    @staticmethod
    def transfer_funds(source_wallet_id, target_wallet_id, amount):
        conn = DatabaseManager.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT balance FROM wallets WHERE walletid = %s FOR UPDATE;", (source_wallet_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False, "Source wallet not found"
                    source_balance = row[0]

                    if source_balance < amount:
                        return False, "Insufficient funds in source wallet"

                    cursor.execute("SELECT 1 FROM wallets WHERE walletid = %s;", (target_wallet_id,))
                    if not cursor.fetchone():
                        return False, "Target wallet not found"

                    cursor.execute("UPDATE wallets SET balance = balance - %s WHERE walletid = %s;",
                                   (amount, source_wallet_id))
                    cursor.execute("UPDATE wallets SET balance = balance + %s WHERE walletid = %s;",
                                   (amount, target_wallet_id))

                    cursor.execute("""
                        INSERT INTO gametransactions (transactionid, walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
                        VALUES (
                            (SELECT COALESCE(MAX(transactionid), 8000) + 1 FROM gametransactions),
                            %s, CURRENT_DATE, %s, 'Transfer Out', %s, 'System'
                        );
                    """, (source_wallet_id, -amount, f"Wallet {target_wallet_id}"))

                    cursor.execute("""
                        INSERT INTO gametransactions (transactionid, walletid, transactiondate, amount, transactiontype, recipient, paymentmethod)
                        VALUES (
                            (SELECT COALESCE(MAX(transactionid), 8000) + 1 FROM gametransactions),
                            %s, CURRENT_DATE, %s, 'Transfer In', %s, 'System'
                        );
                    """, (target_wallet_id, amount, f"Wallet {source_wallet_id}"))

            return True, "Transfer successful"
        except Exception as e:
            return False, f"Transfer failed: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def authenticate_player(email, password):
        query = "SELECT playerid, firstname, lastname, email, isactive FROM players WHERE email = %s;"
        success, result = DatabaseManager.execute_query(query, (email,), fetch=True)
        if success and result:
            player = result[0]
            player_id, firstname, lastname, db_email, is_active = player
            if not is_active:
                return False, "Account is deactivated. Cannot log in."
            return True, {"role": "Player", "playerid": player_id, "name": f"{firstname} {lastname}"}
        return False, "Invalid email or password"

    @staticmethod
    def verify_wallet_ownership(player_id, wallet_id, required_roles=("Owner", "Co-Owner")):
        """
        Verifies if a player holds a specific role for a wallet.
        Members can view but not transact; Owners/Co-Owners can transact.
        """
        query = "SELECT holderrole FROM walletholders WHERE playerid = %s AND walletid = %s;"
        success, result = DatabaseManager.execute_query(query, (player_id, wallet_id), fetch=True)
        if success and result:
            role = result[0][0]
            if role in required_roles:
                return True, role
            return False, f"Access denied: Role '{role}' cannot perform this action."
        return False, "Player does not hold this wallet."

    @staticmethod
    def submit_wallet_review(player_id, wallet_id, rating, comment=None):
        check_query = "SELECT 1 FROM walletreviews WHERE playerid = %s AND walletid = %s;"
        ok, existing = DatabaseManager.execute_query(check_query, (player_id, wallet_id), fetch=True)
        if ok and existing:
            return False, "Duplicate review rejected: You have already reviewed this wallet."

        insert_query = """
                INSERT INTO walletreviews (
                    reviewid, playerid, walletid, rating, reviewtext, reviewdate, isverified
                )
                VALUES (
                    (SELECT COALESCE(MAX(reviewid), 0) + 1 FROM walletreviews),
                    %s, %s, %s, %s, CURRENT_DATE, FALSE
                )
                RETURNING reviewid;
            """
        success, result = DatabaseManager.execute_query(
            insert_query, (player_id, wallet_id, rating, comment), fetch=True
        )
        if success and result:
            return True, result[0][0]
        return False, result or "Failed to submit review."

    @staticmethod
    def get_average_rating_per_wallet_type():
        query = """
            SELECT w.wallettype, AVG(r.rating) as avg_rating
            FROM wallets w
            JOIN walletreviews r ON w.walletid = r.walletid
            WHERE r.rating IS NOT NULL
            GROUP BY w.wallettype;
        """
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, "Failed to calculate average ratings"

    @staticmethod
    def project_wallet_bonus(wallet_id):
        query = "SELECT balance, bonusrate FROM wallets WHERE walletid = %s;"
        success, result = DatabaseManager.execute_query(query, (wallet_id,), fetch=True)
        if not success or not result:
            return False, "Wallet not found"

        balance, annual_bonus_rate = result[0]
        monthly_rate = (float(annual_bonus_rate) / 100.0) / 12.0

        projections = {
            "1_month": float(balance) * (1 + monthly_rate * 1),
            "6_months": float(balance) * (1 + monthly_rate * 6),
            "12_months": float(balance) * (1 + monthly_rate * 12)
        }
        return True, projections

    @staticmethod
    def open_wallet(player_id, wallet_type, hub_id, balance, minimum_balance, bonus_rate, description):
        conn = DatabaseManager.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM players WHERE playerid = %s;", (player_id,))
                    if not cursor.fetchone():
                        return False, "Player not found"

                    cursor.execute("SELECT 1 FROM gaminghubs WHERE hubid = %s;", (hub_id,))
                    if not cursor.fetchone():
                        return False, "Gaming hub not found"

                    cursor.execute(
                        """
                        INSERT INTO wallets (
                            walletid, wallettype, hubid, balance, bonusrate,
                            walletdescription, opendate, minimumbalance, isactive
                        )
                        VALUES (
                            (SELECT COALESCE(MAX(walletid), 0) + 1 FROM wallets),
                            %s, %s, %s, %s, %s, CURRENT_DATE, %s, TRUE
                        )
                        RETURNING walletid;
                        """,
                        (wallet_type, hub_id, balance, bonus_rate, description, minimum_balance),
                    )
                    wallet_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO walletholders (walletid, playerid, holderrole)
                        VALUES (%s, %s, 'Owner');
                        """,
                        (wallet_id, player_id),
                    )

            return True, wallet_id
        except Exception as e:
            err_msg = getattr(e, "pgerror", None) or str(e)
            err_msg = err_msg.split("\n")[0].replace("ERROR:  ", "")
            return False, f"Failed to open wallet: {err_msg}"
        finally:
            conn.close()

    @staticmethod
    def update_wallet(wallet_id, bonus_rate, description):
        query = """
                UPDATE wallets
                SET bonusrate = %s, walletdescription = %s
                WHERE walletid = %s
                RETURNING walletid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bonus_rate, description, wallet_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Wallet not found"
        return False, result

    @staticmethod
    def set_wallet_active(wallet_id, active):
        query = """
                UPDATE wallets
                SET isactive = %s
                WHERE walletid = %s
                RETURNING walletid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bool(active), wallet_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Wallet not found"
        return False, result

    @staticmethod
    def wallet_inventory():
        query = """
                SELECT
                    wallettype,
                    COUNT(*) AS wallet_count,
                    COUNT(*) FILTER (WHERE isactive) AS active_count,
                    COALESCE(SUM(balance), 0) AS total_balance,
                    COALESCE(AVG(balance), 0) AS avg_balance
                FROM wallets
                GROUP BY wallettype
                ORDER BY wallettype;
            """
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, result or "Failed to load wallet inventory"

    @staticmethod
    def open_wallet(player_id, wallet_type, hub_id, balance, minimum_balance, bonus_rate, description):
        conn = DatabaseManager.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM players WHERE playerid = %s;", (player_id,))
                    if not cursor.fetchone():
                        return False, "Player not found"

                    cursor.execute("SELECT 1 FROM gaminghubs WHERE hubid = %s;", (hub_id,))
                    if not cursor.fetchone():
                        return False, "Gaming hub not found"

                    cursor.execute(
                        """
                        INSERT INTO wallets (
                            walletid, wallettype, hubid, balance, bonusrate,
                            walletdescription, opendate, minimumbalance, isactive
                        )
                        VALUES (
                            (SELECT COALESCE(MAX(walletid), 0) + 1 FROM wallets),
                            %s, %s, %s, %s, %s, CURRENT_DATE, %s, TRUE
                        )
                        RETURNING walletid;
                        """,
                        (wallet_type, hub_id, balance, bonus_rate, description, minimum_balance),
                    )
                    wallet_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO walletholders (walletid, playerid, holderrole, joindate, depositamount)
                        VALUES (%s, %s, 'Owner', CURRENT_DATE, %s);
                        """,
                        (wallet_id, player_id, balance),
                    )

            return True, wallet_id
        except Exception as e:
            err_msg = getattr(e, "pgerror", None) or str(e)
            err_msg = err_msg.split("\n")[0].replace("ERROR:  ", "")
            return False, f"Failed to open wallet: {err_msg}"
        finally:
            conn.close()

    @staticmethod
    def update_wallet(wallet_id, bonus_rate, description):
        query = """
                UPDATE wallets
                SET bonusrate = %s, walletdescription = %s
                WHERE walletid = %s
                RETURNING walletid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bonus_rate, description, wallet_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Wallet not found"
        return False, result

    @staticmethod
    def set_wallet_active(wallet_id, active):
        query = """
                UPDATE wallets
                SET isactive = %s
                WHERE walletid = %s
                RETURNING walletid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bool(active), wallet_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Wallet not found"
        return False, result

    @staticmethod
    def wallet_inventory():
        query = """
                SELECT
                    wallettype,
                    COUNT(*) AS wallet_count,
                    COUNT(*) FILTER (WHERE isactive) AS active_count,
                    COALESCE(SUM(balance), 0) AS total_balance,
                    COALESCE(AVG(balance), 0) AS avg_balance
                FROM wallets
                GROUP BY wallettype
                ORDER BY wallettype;
            """
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, result or "Failed to load wallet inventory"

    @staticmethod
    def add_hub(hub_name, location):
        query = """
                INSERT INTO gaminghubs (hubid, hubname, location, isactive)
                VALUES (
                    (SELECT COALESCE(MAX(hubid), 0) + 1 FROM gaminghubs),
                    %s, %s, TRUE
                )
                RETURNING hubid;
            """
        success, result = DatabaseManager.execute_query(query, (hub_name, location), fetch=True)
        if success and result:
            return True, result[0][0]
        return False, result or "Failed to add hub"

    @staticmethod
    def update_hub(hub_id, hub_name, location):
        query = """
                UPDATE gaminghubs
                SET hubname = %s, location = %s
                WHERE hubid = %s
                RETURNING hubid;
            """
        success, result = DatabaseManager.execute_query(
            query, (hub_name, location, hub_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Hub not found"
        return False, result

    @staticmethod
    def set_hub_active(hub_id, active):
        conn = DatabaseManager.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn:
                with conn.cursor() as cursor:
                    if not active:
                        cursor.execute(
                            "SELECT COUNT(*) FROM wallets WHERE hubid = %s AND isactive = TRUE;",
                            (hub_id,),
                        )
                        active_wallets = cursor.fetchone()[0]
                        if active_wallets > 0:
                            return False, "Cannot deactivate hub with active wallets"

                    cursor.execute(
                        """
                        UPDATE gaminghubs
                        SET isactive = %s
                        WHERE hubid = %s
                        RETURNING hubid;
                        """,
                        (bool(active), hub_id),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return False, "Hub not found"
            return True, row[0]
        except Exception as e:
            err_msg = getattr(e, "pgerror", None) or str(e)
            err_msg = err_msg.split("\n")[0].replace("ERROR:  ", "")
            return False, f"Failed to update hub status: {err_msg}"
        finally:
            conn.close()

    @staticmethod
    def get_hub_details(hub_id):
        query = """
                SELECT
                    h.hubid,
                    h.hubname,
                    h.location,
                    h.isactive,
                    COUNT(w.walletid) AS wallet_count,
                    COUNT(w.walletid) FILTER (WHERE w.isactive) AS active_wallets,
                    COALESCE(SUM(w.balance), 0) AS total_balance,
                    COALESCE(AVG(w.bonusrate), 0) AS avg_bonus_rate
                FROM gaminghubs h
                LEFT JOIN wallets w ON w.hubid = h.hubid
                WHERE h.hubid = %s
                GROUP BY h.hubid, h.hubname, h.location, h.isactive;
            """
        success, result = DatabaseManager.execute_query(query, (hub_id,), fetch=True)
        if success and result:
            return True, result[0]
        if success:
            return False, "Hub not found"
        return False, result

    @staticmethod
    def hub_summary_report():
        query = """
                SELECT
                    h.hubid,
                    h.hubname,
                    h.location,
                    h.isactive,
                    COUNT(w.walletid) AS wallet_count,
                    COUNT(w.walletid) FILTER (WHERE w.isactive) AS active_wallets,
                    COALESCE(SUM(w.balance), 0) AS total_balance,
                    COALESCE(AVG(w.bonusrate), 0) AS avg_bonus_rate
                FROM gaminghubs h
                LEFT JOIN wallets w ON w.hubid = h.hubid
                GROUP BY h.hubid, h.hubname, h.location, h.isactive
                ORDER BY h.hubid;
            """
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, result or "Failed to load hub summary report"

    @staticmethod
    def reverse_transaction(transaction_id):
        conn = DatabaseManager.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT transactionid, walletid, amount, transactiontype, recipient, paymentmethod
                        FROM gametransactions
                        WHERE transactionid = %s
                        FOR UPDATE;
                        """,
                        (transaction_id,),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return False, "Transaction not found"

                    _, wallet_id, amount, tx_type, _, payment_method = row

                    if tx_type == "Reversal":
                        return False, "Cannot reverse a reversal transaction"

                    marker = f"Reversal of #{transaction_id}"
                    cursor.execute(
                        """
                        SELECT 1 FROM gametransactions
                        WHERE walletid = %s AND transactiontype = 'Reversal' AND recipient = %s;
                        """,
                        (wallet_id, marker),
                    )
                    if cursor.fetchone():
                        return False, f"Transaction #{transaction_id} has already been reversed"

                    cursor.execute(
                        "SELECT balance, minimumbalance FROM wallets WHERE walletid = %s FOR UPDATE;",
                        (wallet_id,),
                    )
                    wallet_row = cursor.fetchone()
                    if not wallet_row:
                        return False, "Wallet not found"

                    current_balance, min_balance = wallet_row
                    reversal_amount = -amount
                    new_balance = current_balance + reversal_amount

                    if new_balance < min_balance:
                        return False, "Reversal would drop wallet balance below minimum balance"

                    cursor.execute(
                        "UPDATE wallets SET balance = %s WHERE walletid = %s;",
                        (new_balance, wallet_id),
                    )
                    cursor.execute(
                        """
                        INSERT INTO gametransactions (
                            transactionid, walletid, transactiondate, amount,
                            transactiontype, recipient, paymentmethod
                        )
                        VALUES (
                            (SELECT COALESCE(MAX(transactionid), 0) + 1 FROM gametransactions),
                            %s, CURRENT_DATE, %s, 'Reversal', %s, %s
                        )
                        RETURNING transactionid;
                        """,
                        (wallet_id, reversal_amount, marker, payment_method),
                    )
                    rev_id = cursor.fetchone()[0]

            return True, rev_id
        except Exception as e:
            err_msg = getattr(e, "pgerror", None) or str(e)
            err_msg = err_msg.split("\n")[0].replace("ERROR:  ", "")
            return False, f"Failed to reverse transaction: {err_msg}"
        finally:
            conn.close()

    @staticmethod
    def totals_by_payment_method():
        query = """
                SELECT
                    COALESCE(paymentmethod, 'Unspecified') AS payment_method,
                    COUNT(*) AS tx_count,
                    COALESCE(SUM(amount), 0) AS net_amount,
                    COALESCE(SUM(ABS(amount)), 0) AS gross_volume
                FROM gametransactions
                GROUP BY COALESCE(paymentmethod, 'Unspecified')
                ORDER BY gross_volume DESC, payment_method;
            """
        success, result = DatabaseManager.execute_query(query, fetch=True)
        if success:
            return True, result
        return False, result or "Failed to load totals by payment method"

    @staticmethod
    def set_player_active(player_id, active):
        query = """
                UPDATE players
                SET isactive = %s
                WHERE playerid = %s
                RETURNING playerid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bool(active), player_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Player not found"
        return False, result

    @staticmethod
    def set_review_verified(review_id, verified):
        query = """
                UPDATE walletreviews
                SET isverified = %s
                WHERE reviewid = %s
                RETURNING reviewid;
            """
        success, result = DatabaseManager.execute_query(
            query, (bool(verified), review_id), fetch=True
        )
        if success and result:
            return True, result[0][0]
        if success:
            return False, "Review not found"
        return False, result