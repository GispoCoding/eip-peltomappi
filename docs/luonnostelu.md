---
editor_options: 
  markdown: 
    wrap: 72
---

# **Karttapiirrokset/luonnostelu**

💡HUOM! Vaatii että projekti on ladattu QGIS-työpöytä ohjelmistoon. Jos
et ole tehnyt tätä vielä noudata ohjeiden kohtaa: [Projektin lataaminen
tietokoneelle
QGIS-työpöytäsovellukseen](https://gispocoding.github.io/eip-peltomappi/projektin_lataaminen.html#projektin-lataaminen-tietokoneelle-qgis-tyopoytasovellukseen)

Mergin Mapsin karttapiirros (Map Sketching) -ominaisuuden avulla
käyttäjä voi piirtää vapaalla kädellä kartan päälle
mobiilisovelluksessa. Piirroksia voi tehdä eri väreillä ja ne
tallentuvat erilliseen kerrokseen, joka synkronoituu takaisin
QGIS-projektiin. Ominaisuus sopii esimerkiksi kenttämuistiinpanojen,
reittien tai huomioiden merkitsemiseen nopeasti ilman, että tarvitsee
luoda varsinaisia kohteita tietokantaan.

## **Työkalun käyttöönotto**

1.  Avaa projekti QGIS-ohjelmassa.

2.  Valitse ylävalikosta ***Projekti → Ominaisuudet.***

3.  Siirry ***Mergin Maps*** -välilehdelle.

4.  Ota käyttöön ***Enable map sketching*** -valintaruutu. Halutessasi
    voit myös määrittää värit, joita mobiilisovelluksessa voi käyttää
    piirroksissa.

5.  Tallenna muutokset. Projektiin luodaan uusi GeoPackage-tiedosto
    nimeltä ***map_sketches.gpkg***, joka sisältää piirroskerroksen.

6.  Synkronoi projekti Mergin Maps -palveluun.

## **Karttapiirrosominaisuuden käyttäminen mobiilisovelluksessa**

1.  Napsauta karttapiirroskuvaketta ***(kynä)*** vasemmassa alakulmassa.

2.  Avautuu piirrosvalikko. Piirrä vapaalla kädellä tai styluksella.

3.  Valitse yksi seitsemästä (oletusväriset) tai projektissa
    määritellyistä väreistä.

4.  Käytä kumityökalua virheiden korjaamiseen ja ***Kumoa***-painiketta
    viimeisen muutoksen perumiseen.

5.  Sulje piirrosnäkymä esimerkiksi vihreällä ***X***-painikkeella.

<iframe src="https://drive.google.com/file/d/1TnyIE0WfYiK_RKHdSKGWvaUlRTl3Wkik/preview" width="50%" height="900" allowfullscreen="allowfullscreen">

</iframe>
