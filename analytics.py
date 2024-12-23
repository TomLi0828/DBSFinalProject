import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

connection_string = """
        Driver={ODBC Driver 18 for SQL Server};
        Server=tcp:scn.database.windows.net,1433;
        Database=SupplyChain;
        Uid=CloudSA10a2445c;
        Pwd=DBProject@2024;  
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
        """
def getDailyOrderAmount():
    global connection_string
    print("Connecting to database...")
    try:

        conn = pyodbc.connect(connection_string)
        print("Connected to the server")

        query = """
        SELECT 
            OrderDate, SUM(TotalAmount) AS TotalAmountSum
        FROM 
            ORDERS
        GROUP BY 
            OrderDate
        ORDER BY 
            OrderDate;
        """

        df = pd.read_sql(query, conn)
        conn.close()
        print("Connection closed")

        plt.figure(figsize=(10, 6))
        plt.plot(df['OrderDate'], df['TotalAmountSum'], marker='o', linestyle='-', label='Total Amount by Date')
        plt.xlabel("Order Date")
        plt.ylabel("Total Amount (Dollar)")
        plt.title("Total Amount by Order Date")
        plt.legend()
        plt.show()

    except Exception as e:
        print("Error occurred:", e)

def plotProductSales():
    global connection_string
    print("Connecting to database...")
    try:


        conn = pyodbc.connect(connection_string)
        print("Connected to the server")

        product_ids = input("Enter product IDs separated by space: ").strip().split()
        for element in product_ids:
            if not element.isdigit():
                print("Invalid product ID input, closing connection...", )
                conn.close()
                print("Connection closed")

                return

        product_ids = ",".join(product_ids)


        query = f"""
        SELECT 
            p.ProductID,
            p.Name AS ProductName,
            SUM(oi.Quantity) AS TotalQuantitySold,
            SUM(oi.Quantity * oi.UnitPrice) AS TotalAmount
        FROM 
            OrderItem oi
        JOIN 
            PRODUCT p ON oi.ProductID = p.ProductID
        WHERE 
            p.ProductID IN ({product_ids})
        GROUP BY 
            p.ProductID, p.Name
        ;
        """

        df = pd.read_sql(query, conn)
        conn.close()
        print("Connection closed")

        if df.empty:
            print("No data found.")
            return

        plt.figure(figsize=(10, 6))
        plt.bar(df['ProductName'], df['TotalQuantitySold'], color='#f2c777', alpha=0.7)
        plt.title("Total Quantity Sold by Product")
        plt.xlabel("Product Name")
        plt.ylabel("Total Quantity Sold")
        plt.show()

        plt.figure(figsize=(10, 6))
        plt.bar(df['ProductName'], df['TotalAmount'], color='#a6a7ed', alpha=0.7)
        plt.title("Total Amount by Product")
        plt.xlabel("Product Name")
        plt.ylabel("Total Amount (Dollar)")
        plt.show()

    except Exception as e:
        print("An error occurred:", e)

def predict_next_week_sales():
    global connection_string
    print("Connecting to database...")
    try:

        conn = pyodbc.connect(connection_string)
        print("Connected to the server")

        product_id = input("Enter ProductID: ").strip()
        if not product_id.isdigit():
            print("Invalid ProductID. Please enter a numeric value.")
            return

        query = f"""
        SELECT 
            Name, OrderDate, SUM(oi.Quantity) AS DailyQuantity
        FROM 
            OrderItem oi
        JOIN 
            ORDERS o ON oi.OrderID = o.OrderID
        JOIN 
            PRODUCT p ON oi.ProductID = p.ProductID
        WHERE 
            oi.ProductID = {product_id}
        GROUP BY 
            OrderDate, Name
        ORDER BY 
            OrderDate;
        """

        df = pd.read_sql(query, conn)
        conn.close()
        print("Connection closed")

        if df.empty:
            print(f"No sales data found for ProductID {product_id}.")
            return

        df['OrderDate'] = pd.to_datetime(df['OrderDate'])
        df.set_index('OrderDate', inplace=True)
        df = df.asfreq('D', fill_value=0)
        model = ARIMA(df['DailyQuantity'], order=(7, 1, 0))
        model_fit = model.fit()

        forecast = model_fit.forecast(steps=7)
        forecast_dates = pd.date_range(df.index[-1] + pd.Timedelta(days=1), periods=7, freq='D')

        forecast_df = pd.DataFrame({'ForecastDate': forecast_dates, 'PredictedQuantity': forecast})
        print(f"\nPredicted total quantity demanded for the upcoming week: {forecast.sum():.1f}")


        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['DailyQuantity'], label='Historical sales quantites', marker='o')
        plt.plot(forecast_dates, forecast, label='Forecast quantities', marker='x', color='red')
        plt.title(f"7 Days Sales Forecast for {df['Name'].iloc[0]}")
        plt.xlabel("Date")
        plt.ylabel("Daily Quantity")
        plt.legend()
        plt.grid()
        plt.show()

    except Exception as e:
        print("An error occurred:", e)