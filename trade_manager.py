
class TradeManager:
  def __init__(self, stop_loss_pct=1.5, take_profit_pct=3.0):
    self.stop_loss_pct=stop_loss_pct
    self.take_profit_pct=take_profit_pct
    self.active_trades=[]
    self.closed_trades=[]
  
  def open_trade(self, entry_price,direction,position_size, confidence):
          trade={
          'entry_price':entry_price,
          'direction':direction,
          'take_profit':self.price_take_profit(entry_price,direction),
          'stop_loss':self.price_stop_loss(entry_price,direction),
          'position_size':position_size,
          'confidence':confidence
          }  
          self.active_trades.append(trade)
        #add to the list the open trade


                    #calucalte stop_loss => price at which the trade will close becauase we're losing money
  def price_stop_loss(self, entry_price,direction):
                if direction==1: #long
                    return entry_price * (1-self.stop_loss_pct/100)
                else:    #short
                    return entry_price * (1+self.stop_loss_pct/100)
                    ##caclulate take_proift=> price at which the trades is closing because we won enough 
  def price_take_profit(self,entry_price,direction):
                if direction==1: #long
                    return entry_price * (1+self.take_profit_pct/100)
                else:#short
                      return entry_price*(1-self.take_profit_pct/100)



  def check_exits(self, current_price):
        #check if current trades hit stop loss/take profit yet
        trades_to_close=[]
        for trade in self.active_trades[:]:
            
            direction=trade['direction']
            stop_loss_price=trade['stop_loss']
            take_profit_price=trade['take_profit']

            #using close_trade to close it+exit_price
            if direction==1:
               hit_tp=current_price>=take_profit_price
               hit_sl=current_price<=stop_loss_price

            else:
               hit_tp=current_price<=take_profit_price
               hit_sl=current_price>=stop_loss_price
            if hit_tp:
                  self.close_trade(trade, current_price, reason='take profit')
                  trades_to_close.append(trade)

            elif hit_sl:
                  self.close_trade(trade,current_price, reason = 'stop loss')
                  trades_to_close.append(trade)


        return trades_to_close




  def close_trade(self, trade,exit_price, reason):
        #closing trades +reason why +PNL

        entry_price=trade['entry_price']
        direction=trade['direction']
        position_size=trade['position_size']

        #calculate price chgange
        if direction==1:#long 
            price_change_pct=(exit_price-entry_price) / entry_price
        else: #short 
            price_change_pct=(entry_price-exit_price) / entry_price

        pnl=price_change_pct*position_size
        
        trade.update({
            'exit_price':exit_price,
            'pnl':pnl,
            'reason':reason
        })
        #move from active to closed
        self.active_trades.remove(trade)
        self.closed_trades.append(trade)
        
