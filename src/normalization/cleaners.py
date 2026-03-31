import polars as pl
from src.utils.logger import get_logger

logger = get_logger(__name__)

def clean_financial_column(col_name: str) -> pl.Expr:
    # procesamos strings de moneda eliminando simbolos y convirtiendo a float64.
    return (
        pl.col(col_name)
        .cast(pl.Utf8)
        .fill_null("0")
        # elimina espacios, simbolos de moneda y letras
        .str.replace_all(r"[^\d\.,]", "")
        # elimina puntos que actuan como separadores de miles
        .str.replace_all(r"\.(?=\d{3}(?:,|$))", "")
        # elimina comas que actuan como separadores de miles
        .str.replace_all(r",(?=\d{3}(?:\.|$))", "")
        # unifica el separador decimal a punto
        .str.replace(",", ".")
        .cast(pl.Float64, strict=False)
        .fill_null(0.0)
    )

def normalize_identity(col_name: str) -> pl.Expr:
    # aseguramos que el dni tenga 8 caracteres aplicando padding
    return (
        pl.col(col_name)
        .cast(pl.Utf8)
        .fill_null("")
        # elimina decimales si vino como float ".0"
        .str.replace(r"\.0$", "")
        .str.rjust(8, "0")
    )

def standardize_text(col_name: str, casing: str = "upper") -> pl.Expr:
    # eliminamos espacios dobles, tildes y aplicamos un casing consistente
    expr = (
        pl.col(col_name)
        .cast(pl.Utf8)
        .fill_null("")
        # reemplazo de vocales
        .str.replace_all(r"[ÁÀÄÂ]", "A")
        .str.replace_all(r"[ÉÈËÊ]", "E")
        .str.replace_all(r"[ÍÌÏÎ]", "I")
        .str.replace_all(r"[ÓÒÖÔ]", "O")
        .str.replace_all(r"[ÚÙÜÛ]", "U")
        .str.replace_all(r"[áàäâ]", "a")
        .str.replace_all(r"[éèëê]", "e")
        .str.replace_all(r"[íìïî]", "i")
        .str.replace_all(r"[óòöô]", "o")
        .str.replace_all(r"[úùüû]", "u")
        # eliminacion de espacios multiples y trim
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
    )
    
    if casing.lower() == "upper":
        return expr.str.to_uppercase()
    elif casing.lower() == "title":
        return expr.str.to_titlecase()
    
    return expr