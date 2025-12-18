cols_to_drop_due_to_leakage = [
                "gravidade_leve", "gravidade_grave", "gravidade_ileso", "gravidade_fatal",
                ]
df = df.drop(columns=cols_to_drop_due_to_leakage)
cols_to_drop = [
                    "id_sinistro",
                    "tp_veiculo_nao_disponivel",
                    "gravidade_nao_disponivel",
                    "tp_sinistro_nao_disponivel",
                    "logradouro",
                    "numero_logradouro",
                    "ano_mes_sinistro"
                ]
                
cols_to_drop = [col for col in cols_to_drop if col in df.columns]