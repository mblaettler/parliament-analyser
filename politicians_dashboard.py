import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

from data_loader.Politicians import Politicians


def main():
    politicians_loader = Politicians()

    cantons = politicians_loader.load_cantons()
    st.write("# Wer regiert uns?")
    st.write(
"""
Dieses Dashboard gibt dir die Möglichkeit zu erforschen, von welchen Personen du in den letzten 4 Jahren regiert
wurdest, nebst der offensichtlichen demographischen und geschlechterverteilung werden auch die Berufe und Mandate der
unterschiedlichen Politker und Politikerinnen unter die Lupe genommen. Du kannst untenstehend einstellen, welcher Kanton
und welche Parteien dich interessieren.
"""
    )
    st.write("## Filter")
    cantons_list = ["Alle"] + cantons
    canton_filter = st.selectbox("Kanton", cantons_list)
    canton_filter = canton_filter if canton_filter in cantons else None

    parties = politicians_loader.load_parties(canton_filter)
    parties_filter = st.multiselect("Partei", parties)
    print(parties_filter)

    data = politicians_loader.load_politicians(canton_filter=canton_filter, party_filter=parties_filter)

    data["_source.birthDate"] = pd.to_datetime(data["_source.birthDate"])
    data["age"] = (datetime.now().year - data["_source.birthDate"].dt.year)

    st.write(
"""
## Altersverteilung

Eine interessante Frage ist, wie alt bzw. wie jung unsere Landesvertretung ist. Zur Einordnung ein paar Fakten zur
Altersverteilung aller in der Schweiz wohnenden Personen:

Durchschnittsalter: 42.8 Jahre  
Altersvertielung: [Siehe BFS Grafik](https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung.assetdetail.23104156.html)
"""
    )

    st.plotly_chart(
        px.histogram(data, x="age", color="_source.party", barmode="group", histnorm="percent",
                     title="Altersverteilung pro Partei",
                     labels={
                         "age": "Alter in Jahren",
                         "_source.party": "Partei",
                         "percent": "Prozent [%]"
                     })
    )

    age_by_party = data.groupby(["_source.party"]).mean()["age"]
    age_by_party_fig = px.bar(age_by_party, title="Durchschnittsalter jeder Partei",
                              labels={
                                "_source.party": "Partei",
                                "value": "Durchschnittsalter in Jahren"
                              })
    age_by_party_fig.update_layout(showlegend=False)
    st.plotly_chart(age_by_party_fig)

    st.write(
"""
## Geschlechterverteilung

Du kannst jeweils auf den inneren Kreis klicken, um einen weiteren Filter zu aktivieren. Wenn du bspw. nur die
Geschlechterverteilung der glp sehen möchtest, kannst du im linken Kreis auf den glp Bereich klicken.
"""
    )

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            px.sunburst(data, path=["_source.party", "_source.gender"],
                        title="Geschlecht nach Partei",
                        labels={
                            "m": "M",
                            "f": "F"
                        }), use_container_width=True
        )

    with col2:
        st.plotly_chart(
            px.sunburst(data, path=["_source.gender", "_source.party"],
                        title="Partei nach Geschlecht"), use_container_width=True
        )


if __name__ == "__main__":
    main()
