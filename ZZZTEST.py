from yahooquery import search

query = "Tesla"
resultados = search(query)

for item in resultados.get("quotes", []):
    simbolo = item.get("symbol")
    nombre = item.get("shortname", "")
    print(f"{simbolo} - {nombre}")
