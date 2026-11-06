"""Sugerencia TF-IDF experimental de categoría, sin aplicar corrección."""

from .auth_contracts import object_response


def apply_category_suggestion_contract(path, method, operation):
    if (
        path != "/api/companies/{company_id}/movements/{transaction_id}/category-suggestion/"
        or method != "get"
    ):
        return
    operation["x-contract-status"] = "category-suggestion-fields-documented"
    operation["responses"].pop("2XX", None)
    operation["description"] = (
        "Todos los miembros. Entrena con hasta 1000 movimientos manualmente clasificados, "
        "más recientes, de la empresa y mismo sentido. Excluye el movimiento objetivo, su "
        "descripción normalizada y Otros. Requiere dos categorías con tres descripciones "
        "distintas cada una; etiquetas contradictorias impiden entrenamiento. "
        "Sugiere con similitud >=0.35 y margen >=0.15; en otro caso se abstiene. "
        "No modifica el movimiento ni crea reglas. Los scores no son probabilidades."
    )
    operation["responses"]["200"] = {
        "description": "Sugerencia o abstención del modelo experimental.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "category": {
                            "type": "string",
                            "nullable": True,
                            "description": "Categoría sugerida o null si se abstiene.",
                        },
                        "similarity": {
                            "type": "number",
                            "description": "Similitud coseno del primer candidato.",
                        },
                        "margin": {
                            "type": "number",
                            "description": "Diferencia entre los dos primeros scores.",
                        },
                        "status": {"type": "string", "enum": ["suggested", "abstained"]},
                        "examples": {
                            "type": "integer",
                            "minimum": 6,
                            "description": "Descripciones distintas usadas para entrenar.",
                        },
                        "notice": {"type": "string"},
                    }
                )
            }
        },
    }
    for code, description in {
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa/membresía o movimiento no encontrado en su tenant.",
        "409": "Sin dirección financiera o entrenamiento no disponible.",
    }.items():
        fields = {"detail": {"type": "string"}}
        if code == "409":
            fields["status"] = {"type": "string", "enum": ["unavailable"]}
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": object_response(fields)}},
        }
