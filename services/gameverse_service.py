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