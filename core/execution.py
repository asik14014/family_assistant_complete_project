# адаптер биржи (ccxtpro)
class ExecutionAdapter:
    """Оборачивает работу с биржей: размещение/отмена/статус ордеров."""
    def __init__(self, client):
        self.client = client

    def buy_market(self, symbol: str, qty: float):
        # TODO: вызвать ccxtpro/REST
        return {"orderId": "mock", "status": "filled"}

    def sell_market(self, symbol: str, qty: float):
        return {"orderId": "mock", "status": "filled"}
