"""Tableau de bord TVA — Meridian Distribution."""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Référentiel TVA — Meridian", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def charger_donnees():
    df = pd.read_csv(
        "data/resultats_vies.csv", parse_dates=["date_saisie", "date_verification"]
    )
    df["etape_rejet"] = df["etape_rejet"].fillna("envoyé à VIES")
    return df


def taux_invalides(donnees, colonne):
    """Calcule la part de numéros invalides (%) pour chaque valeur de `colonne`."""
    return (
        donnees.groupby(colonne)["statut"]
        .apply(lambda statuts: round((statuts == "invalide").mean() * 100, 1))
        .sort_values()
        .reset_index(name="taux d'erreur (%)")
    )


df = charger_donnees()

# =============================================================================
# Barre latérale : Filtres cumulatifs
# =============================================================================
st.sidebar.header("Filtres")
st.sidebar.caption("Les filtres se cumulent et mettent à jour toute la page.")

pays = st.sidebar.multiselect("Pays déclaré", sorted(df["pays_declare"].unique()))
canal = st.sidebar.multiselect("Canal de saisie", sorted(df["source_saisie"].unique()))
debut, fin = st.sidebar.slider(
    "Période de saisie",
    min_value=df["date_saisie"].min().date(),
    max_value=df["date_saisie"].max().date(),
    value=(df["date_saisie"].min().date(), df["date_saisie"].max().date()),
    format="DD/MM/YYYY",
)

selection = df
if pays:
    selection = selection[selection["pays_declare"].isin(pays)]
if canal:
    selection = selection[selection["source_saisie"].isin(canal)]
selection = selection[selection["date_saisie"].dt.date.between(debut, fin)]

st.sidebar.divider()
st.sidebar.caption(f"Lignes affichées : **{len(selection)}** / {len(df)}")

# =============================================================================
# En-tête : Titre, aide et règle métier
# =============================================================================
st.title("Qualité du référentiel TVA")
st.write(
    "Ce tableau de bord suit la validité des numéros de TVA intracommunautaires du référentiel clients. "
    "Utilisez les filtres dans la barre latérale à gauche pour cibler un pays, un canal de saisie ou une période : "
    "tous les indicateurs, graphiques et la liste exportable se mettent à jour automatiquement."
)

derniere = df["date_verification"].max()
st.info(
    f"Dernière vérification VIES : {derniere:%d/%m/%Y à %H:%M}. "
    "Règle : un numéro non tranché ne doit pas être facturé hors taxe tant qu'il n'a pas été revérifié sur VIES."
)

# =============================================================================
# 1. Les quatre chiffres clés
# =============================================================================
total = len(selection)
valides = (selection["statut"] == "valide").sum()
invalides = (selection["statut"] == "invalide").sum()
non_tranches = (selection["statut"] == "non_tranche").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Numéros", total, border=True)
col2.metric("Valides", valides, f"{valides / total:.1%} du total" if total else "0.0%", delta_color="off", border=True)
col3.metric("Invalides", invalides, f"{invalides / total:.1%} du total" if total else "0.0%", delta_color="off", border=True)
col4.metric("Non tranchés", non_tranches, f"{non_tranches / total:.1%} du total" if total else "0.0%", delta_color="off", border=True)

onglet_principal, onglet_avance = st.tabs(["Vue générale & Actions", "Analyses avancées"])

with onglet_principal:
    # =========================================================================
    # 2. L'entonnoir
    # =========================================================================
    with st.container(border=True):
        st.subheader("Combien de numéros ont pu être envoyés à VIES ?")
        absents = (selection["etape_rejet"] == "absent").sum()
        doublons = (selection["etape_rejet"] == "doublon").sum()
        structure = (selection["etape_rejet"] == "structure").sum()

        entonnoir = pd.DataFrame({
            "étape": ["Référentiel", "Sans les absents", "Sans les doublons", "Envoyés à VIES"],
            "numéros": [
                total,
                total - absents,
                total - absents - doublons,
                total - absents - doublons - structure,
            ],
        })
        fig = px.funnel(
            entonnoir,
            x="numéros",
            y="étape",
            title="Du référentiel aux numéros envoyés à VIES",
            color_discrete_sequence=["#4A7C9B"],
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # =========================================================================
    # 3. D'où viennent les erreurs ?
    # =========================================================================
    st.subheader("D'où viennent les erreurs ?")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        with st.container(border=True):
            taux_canal = taux_invalides(selection, "source_saisie")
            taux_canal["alerte"] = taux_canal["source_saisie"].eq("reprise_erp")
            fig_canal = px.bar(
                taux_canal,
                x="taux d'erreur (%)",
                y="source_saisie",
                orientation="h",
                text="taux d'erreur (%)",
                color="alerte",
                color_discrete_map={True: "#D9534F", False: "#4A7C9B"},
                title="Part de numéros invalides par canal de saisie",
            )
            fig_canal.update_traces(texttemplate="%{text} %", textposition="outside", cliponaxis=False)
            fig_canal.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(r=50),
                yaxis_title=None,
            )
            st.plotly_chart(fig_canal, use_container_width=True)

    with col_g2:
        with st.container(border=True):
            taux_pays = taux_invalides(selection, "pays_declare")
            fig_pays = px.bar(
                taux_pays,
                x="taux d'erreur (%)",
                y="pays_declare",
                orientation="h",
                text="taux d'erreur (%)",
                color_discrete_sequence=["#4A7C9B"],
                title="Part de numéros invalides par pays déclaré",
            )
            fig_pays.update_traces(texttemplate="%{text} %", textposition="outside", cliponaxis=False)
            fig_pays.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(r=50),
                yaxis_title=None,
            )
            st.plotly_chart(fig_pays, use_container_width=True)

    st.caption(
        "Le canal reprise_erp se distingue nettement avec près de 59 % de numéros invalides "
        "(contre environ 43 % pour les autres canaux) : il correspond à la reprise de données "
        "historiques depuis l'ancien ERP, importées sans contrôle de format ni vérification VIES."
    )

    st.divider()

    # =========================================================================
    # 4. Les numéros à traiter
    # =========================================================================
    st.subheader("Numéros à traiter")
    a_traiter = selection[selection["statut"] != "valide"].copy()
    a_traiter["action"] = a_traiter["statut"].map({
        "invalide": "Demander un nouveau numéro au client",
        "non_tranche": "Revérifier sur VIES avant la prochaine facture",
    })

    colonnes = ["raison_sociale", "numero_saisi", "pays_declare", "statut", "motif", "action"]
    st.write(f"**{len(a_traiter)}** numéros demandent une action.")
    st.dataframe(
        a_traiter[colonnes],
        hide_index=True,
        use_container_width=True,
        column_config={
            "raison_sociale": "Raison sociale",
            "numero_saisi": "Numéro saisi",
            "pays_declare": "Pays déclaré",
            "statut": "Statut",
            "motif": "Motif",
            "action": "Action recommandée",
        },
    )

    st.download_button(
        "Télécharger la liste pour Excel (.csv)",
        a_traiter[colonnes].to_csv(index=False, sep=";").encode("utf-8-sig"),
        file_name="numeros_a_traiter.csv",
        type="primary",
    )

    with st.expander("Voir toutes les données"):
        st.dataframe(selection, hide_index=True, use_container_width=True)

with onglet_avance:
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        with st.container(border=True):
            temps = selection.dropna(subset=["temps_reponse_ms"])
            if not temps.empty:
                mediane = temps["temps_reponse_ms"].median()
                fig_temps = px.histogram(
                    temps,
                    x="temps_reponse_ms",
                    nbins=30,
                    title="Temps de réponse du service VIES (ms)",
                    color_discrete_sequence=["#4A7C9B"],
                )
                fig_temps.add_vline(
                    x=mediane,
                    line_dash="dash",
                    line_color="#D9534F",
                    annotation_text=f"Médiane : {mediane:.0f} ms",
                )
                fig_temps.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Temps de réponse (ms)",
                    yaxis_title="Nombre d'appels",
                )
                st.plotly_chart(fig_temps, use_container_width=True)
            else:
                st.info("Aucun appel VIES dans la sélection actuelle.")

    with col_a2:
        with st.container(border=True):
            non_tr_pays = (
                selection[selection["statut"] == "non_tranche"]
                .groupby("pays_declare")
                .size()
                .sort_values()
                .reset_index(name="non tranchés")
            )
            if not non_tr_pays.empty:
                fig_nt = px.bar(
                    non_tr_pays,
                    x="non tranchés",
                    y="pays_declare",
                    orientation="h",
                    text="non tranchés",
                    title="Nombre de numéros non tranchés par pays",
                    color_discrete_sequence=["#E09F3E"],
                )
                fig_nt.update_traces(textposition="outside", cliponaxis=False)
                fig_nt.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(r=40),
                    yaxis_title=None,
                )
                st.plotly_chart(fig_nt, use_container_width=True)
            else:
                st.info("Aucun numéro non tranché dans la sélection actuelle.")

    with st.container(border=True):
        temps_box = selection.dropna(subset=["temps_reponse_ms"])
        if not temps_box.empty:
            fig_box = px.box(
                temps_box,
                x="pays_declare",
                y="temps_reponse_ms",
                title="Dispersion des temps de réponse VIES par pays (boîte à moustaches)",
                color_discrete_sequence=["#4A7C9B"],
            )
            fig_box.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Pays déclaré",
                yaxis_title="Temps de réponse (ms)",
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Aucune donnée de temps de réponse pour afficher la boîte à moustaches.")