import uuid
from typing import List, Dict, Any, Optional
from app.models.device import DeviceConfig, TransportProtocol
from app.models.variable import VariableConfig, VariableType, DataType, SimMode
from app.core.scada_synoptics import get_scada_synoptic_html

# Palette de couleurs contrastées pour les courbes et jauges (charte technique sombre)
PALETTE_COLORS = [
    "#E2001A",  # Rouge primaire technique
    "#3B82F6",  # Bleu vif
    "#10B981",  # Émeraude
    "#F59E0B",  # Ambre
    "#8B5CF6",  # Violet
    "#06B6D4",  # Cyan
    "#EC4899",  # Rose
    "#84CC16",  # Lime
    "#F97316",  # Orange
    "#14B8A6",  # Teal
]

def get_clean_var_key(variable: VariableConfig) -> str:
    """Extrait la clé métrique sans le préfixe unique équipement interne du simulateur."""
    if variable.device_id and variable.id.startswith(f"{variable.device_id}_"):
        return variable.id[len(variable.device_id) + 1:]
    return variable.id

def generate_thingsboard_dashboard(device: DeviceConfig, variables: List[VariableConfig]) -> Dict[str, Any]:
    """
    Génère un fichier de configuration JSON complet de tableau de bord ThingsBoard (v3.x / v3.5 - v3.8+),
    prêt à être importé dans ThingsBoard Community ou Professional Edition.

    Le tableau de bord est nativement configuré avec :
    - L'identifiant, le nom et le token ThingsBoard de l'équipement.
    - Une carte d'information affichant les identifiants et protocoles.
    - Des jauges numériques ou radiales pour chaque grandeur physique analogique.
    - Un graphique temporel multi-courbes en temps réel pour toutes les télémétries.
    - Une carte récapitulative des dernières valeurs et attributs.
    - L'alias d'entité configuré par nom d'équipement avec fallback d'association.
    """
    alias_id = str(uuid.uuid4())
    device_name = device.name or device.id
    token_str = device.token or "NON_RENSEIGNE"
    proto_str = device.protocol.value.upper() if hasattr(device.protocol, "value") else str(device.protocol).upper()

    # Classification des variables
    telemetry_vars = [v for v in variables if v.var_type == VariableType.TELEMETRY and v.enabled]
    attribute_vars = [v for v in variables if v.var_type == VariableType.ATTRIBUTE and v.enabled]
    numeric_vars = [v for v in telemetry_vars if v.data_type in (DataType.FLOAT, DataType.INTEGER)]
    other_telemetry_vars = [v for v in telemetry_vars if v.data_type not in (DataType.FLOAT, DataType.INTEGER)]

    widgets: Dict[str, Any] = {}
    layout_widgets: Dict[str, Any] = {}
    current_row = 0

    # -------------------------------------------------------------
    # 1. Widget Bannière d'Information Équipement & Token (HTML Card)
    # -------------------------------------------------------------
    header_widget_id = str(uuid.uuid4())
    header_html = f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 15px; padding: 12px 18px; background: linear-gradient(135deg, #181D26 0%, #12151B 100%); border-radius: 12px; border: 1px solid #2B3342; color: #F1F5F9; font-family: system-ui, -apple-system, sans-serif;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="background: rgba(226, 0, 26, 0.15); border: 1px solid #E2001A; border-radius: 10px; padding: 8px 12px; font-size: 20px; font-weight: bold; color: #E2001A;">
          IoT
        </div>
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.02em;">{device_name}</div>
          <div style="font-size: 12px; color: #94A3B8; font-family: monospace;">ID Technique: {device.id}</div>
        </div>
      </div>

      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 12px; font-size: 12px;">
        <div style="background: #202531; border: 1px solid #2B3342; border-radius: 8px; padding: 6px 12px;">
          <span style="color: #94A3B8;">Protocole:</span>
          <strong style="color: #38BDF8; margin-left: 4px;">{proto_str}</strong>
        </div>
        <div style="background: #202531; border: 1px solid #2B3342; border-radius: 8px; padding: 6px 12px;">
          <span style="color: #94A3B8;">Access Token ThingsBoard:</span>
          <strong style="color: #FBBF24; font-family: monospace; margin-left: 4px;">{token_str}</strong>
        </div>
        <div style="background: #202531; border: 1px solid #2B3342; border-radius: 8px; padding: 6px 12px;">
          <span style="color: #94A3B8;">Cadence:</span>
          <strong style="color: #34D399; margin-left: 4px;">{f'{device.publish_interval}s' if device.publish_interval else 'Par variable'}</strong>
        </div>
      </div>
    </div>
    """

    widgets[header_widget_id] = {
        "typeFullFqn": "system.cards.html_card",
        "isSystemType": True,
        "bundleAlias": "cards",
        "typeAlias": "html_card",
        "type": "static",
        "title": f"Informations Équipement - {device_name}",
        "sizeX": 24,
        "sizeY": 3,
        "config": {
            "datasources": [],
            "settings": {
                "cardHtml": header_html,
                "html": header_html,
                "cardCss": "border-radius: 12px; border: 1px solid #2B3342; background: transparent;"
            },
            "showTitle": False,
            "dropShadow": True,
            "enableFullscreen": False,
            "backgroundColor": "transparent",
            "color": "#F1F5F9",
            "widgetStyle": {
                "background": "transparent"
            }
        },
        "row": current_row,
        "col": 0,
        "id": header_widget_id
    }
    layout_widgets[header_widget_id] = {
        "sizeX": 24,
        "sizeY": 3,
        "row": current_row,
        "col": 0
    }
    current_row += 3

    # -------------------------------------------------------------
    # 2. Widget Schéma Synoptique SCADA (P&ID / SLD / GTB Mimic)
    # -------------------------------------------------------------
    scada_synoptic_id = str(uuid.uuid4())
    synoptic_html = get_scada_synoptic_html(device, variables)

    widgets[scada_synoptic_id] = {
        "typeFullFqn": "system.cards.html_card",
        "isSystemType": True,
        "bundleAlias": "cards",
        "typeAlias": "html_card",
        "type": "static",
        "title": f"Synoptique SCADA Process - {device_name}",
        "sizeX": 24,
        "sizeY": 8,
        "config": {
            "datasources": [],
            "settings": {
                "cardHtml": synoptic_html,
                "html": synoptic_html,
                "cardCss": "border-radius: 12px; border: 1px solid #1E293B; background: transparent; padding: 0;"
            },
            "showTitle": False,
            "dropShadow": True,
            "enableFullscreen": True,
            "backgroundColor": "transparent",
            "color": "#F1F5F9",
            "widgetStyle": {
                "background": "transparent"
            }
        },
        "row": current_row,
        "col": 0,
        "id": scada_synoptic_id
    }
    layout_widgets[scada_synoptic_id] = {
        "sizeX": 24,
        "sizeY": 8,
        "row": current_row,
        "col": 0
    }
    current_row += 8

    # -------------------------------------------------------------
    # 3. Widgets Jauges Numériques pour les grandeurs analogiques
    # -------------------------------------------------------------
    # On affiche jusqu'à 4 jauges sur une ligne (largeur 6 colonnes par jauge sur un total de 24)
    if numeric_vars:
        col_cursor = 0
        gauge_height = 5
        gauge_width = 6 if len(numeric_vars) >= 4 else (8 if len(numeric_vars) == 3 else 12)

        for i, var in enumerate(numeric_vars[:8]):  # Limiter aux 8 premières grandeurs clés pour les jauges
            gauge_id = str(uuid.uuid4())
            color = PALETTE_COLORS[i % len(PALETTE_COLORS)]
            min_val = 0.0
            max_val = 100.0
            if var.math_config:
                if var.math_config.min_val is not None:
                    min_val = float(var.math_config.min_val)
                if var.math_config.max_val is not None:
                    max_val = float(var.math_config.max_val)
                # Marge pour affichage esthétique
                span = max(max_val - min_val, 1.0)
                min_display = round(min_val - 0.1 * span, 1)
                max_display = round(max_val + 0.1 * span, 1)
            else:
                min_display = 0.0
                max_display = 100.0

            datakey = {
                "name": get_clean_var_key(var),
                "type": "timeseries",
                "label": var.name,
                "color": color,
                "units": var.unit or "",
                "decimals": 2 if var.data_type == DataType.FLOAT else 0,
                "settings": {}
            }

            widgets[gauge_id] = {
                "typeFullFqn": "system.digital_gauges.simple_gauge_justgage",
                "isSystemType": True,
                "bundleAlias": "digital_gauges",
                "typeAlias": "simple_gauge_justgage",
                "type": "latest",
                "title": var.name,
                "sizeX": gauge_width,
                "sizeY": gauge_height,
                "config": {
                    "datasources": [
                        {
                            "type": "entity",
                            "entityAliasId": alias_id,
                            "dataKeys": [datakey]
                        }
                    ],
                    "settings": {
                        "minValue": min_display,
                        "maxValue": max_display,
                        "gaugeType": "arc",
                        "showTitle": True,
                        "title": var.name,
                        "unitTitle": var.unit or "",
                        "decimals": 2 if var.data_type == DataType.FLOAT else 0,
                        "gaugeWidthScale": 0.8,
                        "gaugeColor": "#202531",
                        "colorCounter": color,
                        "levelColors": ["#10B981", "#F59E0B", color]
                    },
                    "showTitle": True,
                    "title": var.name,
                    "dropShadow": True,
                    "enableFullscreen": True,
                    "widgetStyle": {
                        "backgroundColor": "#181D26",
                        "borderRadius": "12px",
                        "border": "1px solid #2B3342"
                    }
                },
                "row": current_row,
                "col": col_cursor,
                "id": gauge_id
            }
            layout_widgets[gauge_id] = {
                "sizeX": gauge_width,
                "sizeY": gauge_height,
                "row": current_row,
                "col": col_cursor
            }

            col_cursor += gauge_width
            if col_cursor >= 24:
                col_cursor = 0
                current_row += gauge_height

        if col_cursor > 0:
            current_row += gauge_height

    # -------------------------------------------------------------
    # 3. Graphique Temporel Multi-Courbes (Timeseries Line Chart)
    # -------------------------------------------------------------
    if telemetry_vars:
        chart_id = str(uuid.uuid4())
        chart_datakeys = []
        for i, var in enumerate(telemetry_vars):
            color = PALETTE_COLORS[i % len(PALETTE_COLORS)]
            chart_datakeys.append({
                "name": get_clean_var_key(var),
                "type": "timeseries",
                "label": f"{var.name} ({var.unit})" if var.unit else var.name,
                "color": color,
                "units": var.unit or "",
                "decimals": 2 if var.data_type == DataType.FLOAT else 0,
                "settings": {
                    "showLines": True,
                    "fillLines": False,
                    "showPoints": False,
                    "lineWidth": 2
                }
            })

        chart_width = 16 if attribute_vars or other_telemetry_vars else 24
        chart_height = 8

        widgets[chart_id] = {
            "typeFullFqn": "system.charts.basic_timeseries",
            "isSystemType": True,
            "bundleAlias": "charts",
            "typeAlias": "basic_timeseries",
            "type": "timeseries",
            "title": f"Télémétries en Temps Réel - {device_name}",
            "sizeX": chart_width,
            "sizeY": chart_height,
            "config": {
                "datasources": [
                    {
                        "type": "entity",
                        "entityAliasId": alias_id,
                        "dataKeys": chart_datakeys
                    }
                ],
                "timewindow": {
                    "realtime": {
                        "timewindowMs": 120000,  # Fenêtre 2 minutes glissantes
                        "quickInterval": "CURRENT_DAY",
                        "interval": 1000
                    },
                    "aggregation": {
                        "type": "NONE",
                        "limit": 500
                    }
                },
                "settings": {
                    "showLegend": True,
                    "legendConfig": {
                        "direction": "row",
                        "position": "bottom",
                        "sortDatakeys": False,
                        "showMin": True,
                        "showMax": True,
                        "showAvg": True,
                        "showCurrent": True
                    },
                    "grid": {
                        "color": "#2B3342",
                        "tickColor": "#2B3342",
                        "verticalLines": True,
                        "horizontalLines": True
                    },
                    "xaxis": {
                        "showLabels": True,
                        "color": "#94A3B8"
                    },
                    "yaxis": {
                        "showLabels": True,
                        "color": "#94A3B8"
                    }
                },
                "showTitle": True,
                "title": f"Évolution Télémétrique ({len(chart_datakeys)} grandeurs)",
                "dropShadow": True,
                "enableFullscreen": True,
                "widgetStyle": {
                    "backgroundColor": "#181D26",
                    "borderRadius": "12px",
                    "border": "1px solid #2B3342"
                }
            },
            "row": current_row,
            "col": 0,
            "id": chart_id
        }
        layout_widgets[chart_id] = {
            "sizeX": chart_width,
            "sizeY": chart_height,
            "row": current_row,
            "col": 0
        }

        # -------------------------------------------------------------
        # 4. Carte des Attributs & États (Latest Values Table)
        # -------------------------------------------------------------
        if attribute_vars or other_telemetry_vars:
            attr_table_id = str(uuid.uuid4())
            attr_datakeys = []
            for v in attribute_vars:
                attr_datakeys.append({
                    "name": get_clean_var_key(v),
                    "type": "attribute",
                    "label": v.name,
                    "color": "#38BDF8",
                    "settings": {}
                })
            for v in other_telemetry_vars:
                attr_datakeys.append({
                    "name": get_clean_var_key(v),
                    "type": "timeseries",
                    "label": v.name,
                    "color": "#34D399",
                    "settings": {}
                })

            widgets[attr_table_id] = {
                "typeFullFqn": "system.cards.entities_table",
                "isSystemType": True,
                "bundleAlias": "cards",
                "typeAlias": "entities_table",
                "type": "latest",
                "title": "Attributs & États Opérationnels",
                "sizeX": 8,
                "sizeY": chart_height,
                "config": {
                    "datasources": [
                        {
                            "type": "entity",
                            "entityAliasId": alias_id,
                            "dataKeys": attr_datakeys
                        }
                    ],
                    "settings": {
                        "entitiesTableWidgetTitle": "Attributs & États Opérationnels",
                        "enableSearch": False,
                        "displayPagination": False,
                        "defaultPageSize": 10
                    },
                    "showTitle": True,
                    "title": "Attributs & États Opérationnels",
                    "dropShadow": True,
                    "enableFullscreen": True,
                    "widgetStyle": {
                        "backgroundColor": "#181D26",
                        "borderRadius": "12px",
                        "border": "1px solid #2B3342"
                    }
                },
                "row": current_row,
                "col": chart_width,
                "id": attr_table_id
            }
            layout_widgets[attr_table_id] = {
                "sizeX": 8,
                "sizeY": chart_height,
                "row": current_row,
                "col": chart_width
            }

        current_row += chart_height

    # -------------------------------------------------------------
    # Configuration Complète du Dashboard ThingsBoard
    # -------------------------------------------------------------
    dashboard_json = {
        "title": f"Supervision SCADA - {device_name}",
        "name": f"Supervision SCADA - {device_name}",
        "configuration": {
            "description": f"Tableau de bord SCADA HMI ThingsBoard pour l'équipement '{device_name}' (ID: {device.id}). Synoptique P&ID / SLD vectoriel animé, instrumentation process et enregistreur de tendance temps réel. Token: {token_str}. Protocole: {proto_str}.",
            "entityAliases": {
                alias_id: {
                    "id": alias_id,
                    "alias": device_name,
                    "filter": {
                        "type": "singleEntity",
                        "singleEntity": {
                            "entityType": "DEVICE",
                            "id": "00000000-0000-0000-0000-000000000000"
                        }
                    }
                }
            },
            "widgets": widgets,
            "states": {
                "default": {
                    "name": "default",
                    "root": True,
                    "layouts": {
                        "main": {
                            "widgets": layout_widgets,
                            "gridSettings": {
                                "columns": 24,
                                "margin": 10,
                                "outerMargin": True,
                                "backgroundColor": "#0F1218",
                                "backgroundSizeMode": "100%",
                                "autoFillHeight": False
                            }
                        }
                    }
                }
            },
            "timewindow": {
                "displayValue": "",
                "hideInterval": False,
                "hideAggregation": False,
                "hideAggInterval": False,
                "realtime": {
                    "realtimeType": 0,
                    "timewindowMs": 120000,
                    "quickInterval": "CURRENT_DAY",
                    "interval": 1000
                },
                "aggregation": {
                    "type": "NONE",
                    "limit": 500
                }
            },
            "settings": {
                "stateControllerId": "entity",
                "showTitle": True,
                "showDashboardsSelect": True,
                "showEntitiesSelect": True,
                "showDashboardTimewindow": True,
                "showDashboardExport": True,
                "toolbarAlwaysOpen": True
            }
        }
    }

    return dashboard_json
