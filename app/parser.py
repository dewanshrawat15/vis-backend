class Transaction:

    def __init__(self, amount, current_balance, mode, transaction_timestamp, transaction_type, txnId):
        self.amount = amount
        self.current_balance = current_balance
        self.mode = mode
        self.transaction_timestamp = transaction_timestamp.split("+")[0]
        self.transaction_type = transaction_type
        self.txn_id = txnId
    
    def get_dict(self):
        return {
            "amount": self.amount,
            "current_balance": self.current_balance,
            "mode": self.mode,
            "transaction_timestamp": self.transaction_timestamp,
            "transaction_type": self.transaction_type,
            "txn_id": self.txn_id
        }
    
def get_transactions(transactions):
    txns = []
    for i in transactions:
        txns.append(Transaction(
            float(i["amount"]), float(i["currentBalance"]), i["mode"], i["transactionTimestamp"], i["type"], i["txnId"]
        ))
    return txns