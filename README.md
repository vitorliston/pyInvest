# pyInvest

Investment tracking software

- Quotes from Yahoo Finance API.
- Rentability and portfolio value tracking.
- Available assets: Stocks (US and BR), REITs and FIIs.
- Position obtained from transactions:
	- Transaction file (data/"filename".txt) must be tab separated.
	- Obligatory columns:
		Date (ex. 28/06/2021),
		Type (US, BR, REIT, FII),	
		Symbol (AMD,WEGE3.SA),
		Order (Buy,Sell),
		Quantity (Transaction amount),
		Price (Asset unitary price, decimal = .),
		Total (Total price paid),
