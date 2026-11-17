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
        query = "SELECT playerid, firstname, lastname, email, phone, isactive FROM players WHERE playerid = %s;"
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
        # Check if player already reviewed this wallet
        check_query = "SELECT 1 FROM walletreviews WHERE playerid = %s AND walletid = %s;"
        success, result = DatabaseManager.execute_query(check_query, (player_id, wallet_id), fetch=True)
        if success and result:
            return False, "Duplicate review rejected: You have already reviewed this wallet."

        insert_query = """
            INSERT INTO walletreviews (playerid, walletid, rating, comment, reviewdate)
            VALUES (%s, %s, %s, %s, CURRENT_DATE);
        """
        success, res = DatabaseManager.execute_query(insert_query, (player_id, wallet_id, rating, comment))
        if success:
            return True, "Review submitted successfully."
        return False, "Failed to submit review."

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