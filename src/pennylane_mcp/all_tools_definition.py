"""Définition de tous les outils MCP Pennylane pour le serveur SSE."""

ALL_TOOLS = [
    # FACTURES CLIENTS
    {
        "name": "pennylane_list_customer_invoices",
        "description": "Liste les factures clients avec pagination et filtres",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "cursor": {"type": "string", "description": "Curseur de pagination"},
                "filter": {"type": "string", "description": "Filtres"},
                "sort": {"type": "string", "description": "Tri", "default": "-id"}
            }
        }
    },
    {
        "name": "pennylane_get_customer_invoice",
        "description": "Récupère une facture client par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "integer", "description": "ID de la facture"}
            },
            "required": ["invoice_id"]
        }
    },
    {
        "name": "pennylane_create_customer_invoice",
        "description": "Crée une nouvelle facture client (brouillon ou finalisée)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "ID du client"},
                "date": {"type": "string", "description": "Date de facture (YYYY-MM-DD)"},
                "deadline": {"type": "string", "description": "Date limite de paiement (YYYY-MM-DD)"},
                "invoice_lines": {
                    "type": "array",
                    "description": "Lignes de facture. Chaque ligne doit contenir: label (string), raw_currency_unit_price (string, ex: '750.00'), quantity (number), unit (string, ex: 'jour'), vat_rate (string, ex: 'FR_200' pour 20%)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string", "description": "Libellé de la ligne"},
                            "raw_currency_unit_price": {"type": "string", "description": "Prix unitaire HT (ex: '750.00')"},
                            "quantity": {"type": "number", "description": "Quantité"},
                            "unit": {"type": "string", "description": "Unité (ex: 'jour', 'unité')"},
                            "vat_rate": {"type": "string", "description": "Taux TVA (ex: 'FR_200' pour 20%, 'FR_100' pour 10%)"},
                            "description": {"type": "string", "description": "Description détaillée (optionnel)"},
                            "section_rank": {"type": "integer", "description": "Rang de section (optionnel)"},
                            "ledger_account_id": {"type": "integer", "description": "ID compte général (optionnel)"},
                            "product_id": {"type": "integer", "description": "ID produit (optionnel)"},
                            "discount": {
                                "type": "object",
                                "description": "Remise sur la ligne (optionnel)",
                                "properties": {
                                    "type": {"type": "string", "description": "Type: 'absolute' ou 'relative'"},
                                    "value": {"type": "string", "description": "Valeur de la remise"}
                                }
                            },
                            "imputation_dates": {
                                "type": "object",
                                "description": "Période d'imputation (optionnel)",
                                "properties": {
                                    "start_date": {"type": "string", "description": "Date de début (YYYY-MM-DD)"},
                                    "end_date": {"type": "string", "description": "Date de fin (YYYY-MM-DD)"}
                                }
                            }
                        },
                        "required": ["label", "raw_currency_unit_price", "quantity", "unit", "vat_rate"]
                    }
                },
                "draft": {"type": "boolean", "description": "true = brouillon modifiable, false = facture finalisée", "default": True},
                "currency": {"type": "string", "description": "Devise (EUR, USD, etc.)", "default": "EUR"},
                "language": {"type": "string", "description": "Langue (fr_FR, en_GB)", "default": "fr_FR"},
                "customer_invoice_template_id": {"type": "integer", "description": "ID du template de facture (optionnel)"},
                "pdf_invoice_subject": {"type": "string", "description": "Titre de la facture (optionnel)"},
                "pdf_description": {"type": "string", "description": "Description de la facture (optionnel)"},
                "pdf_invoice_free_text": {"type": "string", "description": "Texte libre (coordonnées contact, etc.) (optionnel)"},
                "special_mention": {"type": "string", "description": "Mentions spéciales (optionnel)"},
                "external_reference": {"type": "string", "description": "Référence externe unique (optionnel)"},
                "transaction_reference": {
                    "type": "object",
                    "description": "Référence de transaction pour réconciliation automatique (optionnel)",
                    "properties": {
                        "banking_provider": {"type": "string", "description": "Fournisseur bancaire"},
                        "provider_field_name": {"type": "string", "description": "Nom du champ à matcher"},
                        "provider_field_value": {"type": "string", "description": "Valeur à matcher"}
                    }
                },
                "discount": {
                    "type": "object",
                    "description": "Remise globale (optionnel)",
                    "properties": {
                        "type": {"type": "string", "description": "Type: 'absolute' (montant) ou 'relative' (pourcentage)"},
                        "value": {"type": "string", "description": "Valeur de la remise"}
                    }
                },
                "invoice_line_sections": {
                    "type": "array",
                    "description": "Sections de lignes (optionnel)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "rank": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["customer_id", "date", "deadline", "invoice_lines", "draft"]
        }
    },
    # CLIENTS
    {
        "name": "pennylane_list_customers",
        "description": "Liste tous les clients",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20}
            }
        }
    },
    {
        "name": "pennylane_get_customer",
        "description": "Récupère un client par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "ID du client"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "pennylane_create_customer",
        "description": "Crée un nouveau client",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nom du client"},
                "email": {"type": "string", "description": "Email"},
                "customer_type": {"type": "string", "description": "Type: company ou individual"}
            },
            "required": ["name", "customer_type"]
        }
    },
    # DEVIS
    {
        "name": "pennylane_list_quotes",
        "description": "Liste tous les devis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 30}
            }
        }
    },
    {
        "name": "pennylane_get_quote",
        "description": "Récupère un devis par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer", "description": "ID du devis"}
            },
            "required": ["quote_id"]
        }
    },
    {
        "name": "pennylane_create_quote",
        "description": "Crée un nouveau devis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer", "description": "ID du client"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "deadline": {"type": "string", "description": "Date limite (YYYY-MM-DD)"},
                "invoice_lines": {"type": "array", "description": "Lignes du devis"}
            },
            "required": ["customer_id", "date", "deadline", "invoice_lines"]
        }
    },
    {
        "name": "pennylane_update_quote",
        "description": "Met à jour un devis existant",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer", "description": "ID du devis"},
                "deadline": {"type": "string", "description": "Nouvelle date limite"}
            },
            "required": ["quote_id"]
        }
    },
    {
        "name": "pennylane_update_quote_status",
        "description": "Met à jour le statut d'un devis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer", "description": "ID du devis"},
                "status": {"type": "string", "description": "Statut: pending, accepted, denied, invoiced, expired"}
            },
            "required": ["quote_id", "status"]
        }
    },
    # TRANSACTIONS
    {
        "name": "pennylane_list_transactions",
        "description": "Liste toutes les transactions bancaires",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20}
            }
        }
    },
    {
        "name": "pennylane_create_transaction",
        "description": "Crée une nouvelle transaction bancaire",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bank_account_id": {"type": "integer", "description": "ID du compte bancaire"},
                "label": {"type": "string", "description": "Libellé"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "amount": {"type": "string", "description": "Montant"},
                "fee": {"type": "string", "description": "Frais", "default": "0"}
            },
            "required": ["bank_account_id", "label", "date", "amount", "fee"]
        }
    },
    # COMPTABILITÉ
    {
        "name": "pennylane_list_bank_accounts",
        "description": "Liste tous les comptes bancaires",
        "inputSchema": {"type": "object", "properties": {}}
    },
    # FOURNISSEURS
    {
        "name": "pennylane_list_suppliers",
        "description": "Liste tous les fournisseurs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20}
            }
        }
    },
    {
        "name": "pennylane_create_supplier",
        "description": "Crée un nouveau fournisseur",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nom du fournisseur"},
                "email": {"type": "string", "description": "Email"}
            },
            "required": ["name"]
        }
    },
    # JOURNAUX COMPTABLES
    {
        "name": "pennylane_list_journals",
        "description": "Liste tous les journaux comptables",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 25},
                "cursor": {"type": "string", "description": "Curseur de pagination"},
                "filter": {"type": "string", "description": "Filtres (type: eq, not_eq, in, not_in)"},
                "sort": {"type": "string", "description": "Tri", "default": "-id"}
            }
        }
    },
    {
        "name": "pennylane_get_journal",
        "description": "Récupère un journal comptable par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_id": {"type": "integer", "description": "ID du journal"}
            },
            "required": ["journal_id"]
        }
    },
    {
        "name": "pennylane_create_journal",
        "description": "Crée un nouveau journal comptable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code du journal (2 à 5 lettres)"},
                "label": {"type": "string", "description": "Libellé du journal"}
            },
            "required": ["code", "label"]
        }
    },
    # COMPTES GÉNÉRAUX (LEDGER ACCOUNTS)
    {
        "name": "pennylane_list_ledger_accounts",
        "description": "Liste tous les comptes généraux",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1},
                "filter": {"type": "string", "description": "Filtres (id, number, enabled)"}
            }
        }
    },
    {
        "name": "pennylane_get_ledger_account",
        "description": "Récupère un compte général par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "integer", "description": "ID du compte"}
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "pennylane_create_ledger_account",
        "description": "Crée un nouveau compte général. Si le numéro commence par 401 ou 411, un fournisseur/client sera aussi créé",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "Numéro du compte (ex: 401, 411)"},
                "label": {"type": "string", "description": "Libellé du compte"},
                "vat_rate": {"type": "string", "description": "Taux de TVA (ex: FR_200, FR_1_75)"},
                "country_alpha2": {"type": "string", "description": "Code pays (ex: FR)"}
            },
            "required": ["number", "label"]
        }
    },
    # ÉCRITURES COMPTABLES (LEDGER ENTRIES)
    {
        "name": "pennylane_list_ledger_entries",
        "description": "Liste toutes les écritures comptables",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1},
                "filter": {"type": "string", "description": "Filtres (updated_at, created_at, date, journal_id)"},
                "sort": {"type": "string", "description": "Tri", "default": "-updated_at"}
            }
        }
    },
    {
        "name": "pennylane_list_ledger_entry_lines",
        "description": "Liste les lignes d'écriture d'une écriture comptable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ledger_entry_id": {"type": "integer", "description": "ID de l'écriture"},
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1}
            },
            "required": ["ledger_entry_id"]
        }
    },
    {
        "name": "pennylane_create_ledger_entry",
        "description": "Crée une nouvelle écriture comptable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "label": {"type": "string", "description": "Libellé"},
                "journal_id": {"type": "integer", "description": "ID du journal"},
                "ledger_entry_lines": {"type": "array", "description": "Lignes avec debit, credit, ledger_account_id, label"},
                "ledger_attachment_id": {"type": "integer", "description": "ID pièce jointe"},
                "currency": {"type": "string", "description": "Devise", "default": "EUR"}
            },
            "required": ["date", "label", "journal_id", "ledger_entry_lines"]
        }
    },
    {
        "name": "pennylane_update_ledger_entry",
        "description": "Met à jour une écriture comptable",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ledger_entry_id": {"type": "integer", "description": "ID de l'écriture"},
                "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                "label": {"type": "string", "description": "Libellé"},
                "journal_id": {"type": "integer", "description": "ID du journal"},
                "ledger_entry_lines": {"type": "object", "description": "Dict avec create et update"},
                "ledger_attachment_id": {"type": "integer", "description": "ID pièce jointe"},
                "currency": {"type": "string", "description": "Devise"}
            },
            "required": ["ledger_entry_id"]
        }
    },
    # LIGNES D'ÉCRITURE COMPTABLE
    {
        "name": "pennylane_list_all_ledger_entry_lines",
        "description": "Liste toutes les lignes d'écriture",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "cursor": {"type": "string", "description": "Curseur de pagination"},
                "filter": {"type": "string", "description": "Filtres"},
                "sort": {"type": "string", "description": "Tri", "default": "id"}
            }
        }
    },
    {
        "name": "pennylane_get_ledger_entry_line",
        "description": "Récupère une ligne d'écriture par son ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "integer", "description": "ID de la ligne"}
            },
            "required": ["line_id"]
        }
    },
    {
        "name": "pennylane_list_lettered_ledger_entry_lines",
        "description": "Liste les lignes lettrées avec une ligne donnée",
        "inputSchema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "integer", "description": "ID de la ligne"},
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1}
            },
            "required": ["line_id"]
        }
    },
    {
        "name": "pennylane_list_ledger_entry_line_categories",
        "description": "Liste les catégories analytiques d'une ligne",
        "inputSchema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "integer", "description": "ID de la ligne"},
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1}
            },
            "required": ["line_id"]
        }
    },
    {
        "name": "pennylane_link_categories_to_ledger_entry_line",
        "description": "Lie des catégories analytiques à une ligne",
        "inputSchema": {
            "type": "object",
            "properties": {
                "line_id": {"type": "integer", "description": "ID de la ligne"},
                "categories": {"type": "array", "description": "Liste des catégories"}
            },
            "required": ["line_id", "categories"]
        }
    },
    {
        "name": "pennylane_letter_ledger_entry_lines",
        "description": "Lettre des lignes d'écriture ensemble (min 2 lignes)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ledger_entry_lines": {"type": "array", "description": "Liste de lignes avec ID (min 2)"},
                "unbalanced_lettering_strategy": {"type": "string", "description": "none ou partial", "default": "none"}
            },
            "required": ["ledger_entry_lines"]
        }
    },
    {
        "name": "pennylane_unletter_ledger_entry_lines",
        "description": "Délettre des lignes d'écriture (min 1 ligne)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ledger_entry_lines": {"type": "array", "description": "Liste de lignes avec ID (min 1)"},
                "unbalanced_lettering_strategy": {"type": "string", "description": "none ou partial", "default": "none"}
            },
            "required": ["ledger_entry_lines"]
        }
    },
    # BALANCE GÉNÉRALE ET EXERCICES FISCAUX
    {
        "name": "pennylane_get_trial_balance",
        "description": "Récupère la balance générale pour une période donnée",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period_start": {"type": "string", "description": "Date de début (YYYY-MM-DD)"},
                "period_end": {"type": "string", "description": "Date de fin (YYYY-MM-DD)"},
                "is_auxiliary": {"type": "boolean", "description": "Balance auxiliaire", "default": False},
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1}
            },
            "required": ["period_start", "period_end"]
        }
    },
    {
        "name": "pennylane_list_fiscal_years",
        "description": "Liste les exercices fiscaux de l'entreprise",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre de résultats", "default": 20},
                "page": {"type": "integer", "description": "Numéro de page", "default": 1}
            }
        }
    },
    {
        "name": "pennylane_upload_file_attachment",
        "description": "Upload un fichier PDF vers Pennylane. Retourne un file_attachment_id à utiliser dans les endpoints d'import. Fournir soit file_url (URL publique) soit file_base64 (contenu base64).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nom du fichier (ex: 'facture.pdf')", "default": "invoice.pdf"},
                "file_url": {"type": "string", "description": "URL publique du PDF à télécharger et uploader"},
                "file_base64": {"type": "string", "description": "Contenu du PDF encodé en base64"}
            }
        }
    },
    {
        "name": "pennylane_import_customer_invoice",
        "description": "Importe une facture client depuis un PDF uploadé (file_attachment_id). Utiliser après pennylane_upload_file_attachment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_attachment_id": {"type": "integer", "description": "ID retourné par upload_file_attachment"},
                "customer_id": {"type": "integer", "description": "ID du client"},
                "date": {"type": "string", "description": "Date de facture (YYYY-MM-DD)"},
                "deadline": {"type": "string", "description": "Date limite de paiement (YYYY-MM-DD)"},
                "currency_amount_before_tax": {"type": "string", "description": "Total HT (ex: '100.00')"},
                "currency_tax": {"type": "string", "description": "Total TVA (ex: '20.00')"},
                "currency_amount": {"type": "string", "description": "Total TTC (ex: '120.00')"},
                "invoice_lines": {
                    "type": "array",
                    "description": "Lignes de facture",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ledger_account_id": {"type": "integer", "description": "ID compte général (optionnel)"},
                            "currency_amount": {"type": "string", "description": "Montant TTC de la ligne"},
                            "currency_tax": {"type": "string", "description": "TVA de la ligne"},
                            "quantity": {"type": "number", "description": "Quantité"},
                            "raw_currency_unit_price": {"type": "string", "description": "Prix unitaire HT"},
                            "unit": {"type": "string", "description": "Unité (ex: 'jour', 'unité')"},
                            "vat_rate": {"type": "string", "description": "Code TVA (ex: FR_200, FR_100, FR_055, exempt)"}
                        }
                    }
                },
                "currency": {"type": "string", "description": "Devise", "default": "EUR"}
            },
            "required": ["file_attachment_id", "customer_id", "date", "deadline",
                         "currency_amount_before_tax", "currency_tax", "currency_amount", "invoice_lines"]
        }
    },
    {
        "name": "pennylane_import_supplier_invoice",
        "description": "Importe une facture fournisseur depuis un PDF uploadé (file_attachment_id). Utiliser après pennylane_upload_file_attachment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_attachment_id": {"type": "integer", "description": "ID retourné par upload_file_attachment"},
                "supplier_id": {"type": "integer", "description": "ID du fournisseur"},
                "date": {"type": "string", "description": "Date de facture (YYYY-MM-DD)"},
                "deadline": {"type": "string", "description": "Date limite de paiement (YYYY-MM-DD)"},
                "currency_amount_before_tax": {"type": "string", "description": "Total HT (ex: '100.00')"},
                "currency_tax": {"type": "string", "description": "Total TVA (ex: '20.00')"},
                "currency_amount": {"type": "string", "description": "Total TTC (ex: '120.00')"},
                "invoice_lines": {
                    "type": "array",
                    "description": "Lignes de facture fournisseur",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ledger_account_id": {"type": "integer", "description": "ID compte général (optionnel)"},
                            "currency_amount": {"type": "string", "description": "Montant TTC de la ligne"},
                            "currency_tax": {"type": "string", "description": "TVA de la ligne"},
                            "vat_rate": {"type": "string", "description": "Code TVA (ex: FR_200, FR_100, FR_055, exempt)"}
                        }
                    }
                },
                "currency": {"type": "string", "description": "Devise", "default": "EUR"}
            },
            "required": ["file_attachment_id", "supplier_id", "date", "deadline",
                         "currency_amount_before_tax", "currency_tax", "currency_amount", "invoice_lines"]
        }
    },
    {
        "name": "pennylane_create_invoice_from_quote",
        "description": "Crée une facture client à partir d'un devis existant. La facture hérite de toutes les données du devis (client, lignes, montants).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer", "description": "ID du devis à convertir"},
                "draft": {"type": "boolean", "description": "true = brouillon modifiable, false = facture finalisée", "default": True},
                "external_reference": {"type": "string", "description": "Référence externe unique (optionnel)"},
                "customer_invoice_template_id": {"type": "integer", "description": "ID du template de facture (optionnel)"}
            },
            "required": ["quote_id", "draft"]
        }
    },
]
