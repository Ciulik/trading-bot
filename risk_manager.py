class RiskManager():

    def __init__(self,max_open_trades=3, max_daily_loss_pct=0.05, max_risk_trade=0.02):
        self.max_open_trades=max_open_trades
        self.max_daily_loss_pct=max_daily_loss_pct
        self.max_risk_trade=max_risk_trade
        self.daily_loss=0
        pass
    def position_size(self,confidence,balance):
        if 0.50 < confidence <= 0.55:
            return 0.005 * balance
        elif 0.55 < confidence <= 0.60:
            return 0.010 * balance
        elif 0.60 < confidence <= 0.65:
            return 0.015 * balance
        elif confidence > 0.65:
            return 0.020 * balance
        else:
            return 0
        
    def can_open_trade(self, current_open_trades, current_balance, starting_balance):
        if current_open_trades>=self.max_open_trades:
            return False
        daily_loss_pct= (starting_balance-current_balance) / starting_balance

        if daily_loss_pct >=self.max_daily_loss_pct:
            return False
        
        return True
    
