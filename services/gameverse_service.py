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