from supabase_client import supabase

def get_user_by_email(email):
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def get_tickers(user_id):
    res = supabase.table("tickers").select("ticker").eq("user_id", user_id).execute()
    return [r["ticker"] for r in res.data]

def add_ticker(user_id, ticker):
    ticker = ticker.upper()

    try:
        # Verificar si ya existe
        res = supabase.table("tickers").select("id").eq("user_id", user_id).eq("ticker", ticker).execute()
        if res.data and len(res.data) > 0:
            return "exists"

        # Insertar nuevo ticker
        supabase.table("tickers").insert({"user_id": user_id, "ticker": ticker}).execute()
        return "added"

    except Exception as e:
        print(f"Error al agregar ticker: {e}")
        return "error"

def remove_ticker(user_id, ticker):
    supabase.table("tickers").delete().eq("user_id", user_id).eq("ticker", ticker.upper()).execute()
