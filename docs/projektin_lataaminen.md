# **Projektin lataaminen**

## **Projektin lataaminen mobiilisovellukseen**

Kun puhelimessasi on asennettuna [Mergin Maps sovelluksen](https://gispocoding.github.io/eip-peltomappi/esittely.html), toimi seuraavasti:

1.  Avaa sovellus ja napauta oikean yläkulman ikonia:

    <img src="img/aloitusnakyma.jpg" width="34%"/>

2.  Rekisteröi itsellesi tunnukset napauttamalla ***Rekisteröidy***

    <img src="img/register_mergin_maps.png" width="34%"/>

3.  Täytä lomake ja napauta ***Rekisteröidy*** luodaksesi tilisi.

    Saat vahvistussähköpostin, jossa on linkki sähköpostiosoitteesi vahvistamiseksi.

    Tarkista roskapostikansiosi, jos vahvistussähköposti ei näy postilaatikossasi viiden minuutin kuluessa.

4.  Kirjaudu tämän jälkeen tunnuksillasi sisään:

<img src="img/kirjautuminen.jpg" width="34%"/>

Napauta tämän jälkeen alareunan ***Projektit***- kohtaa ja lataa eip-peltomappi- projekti

<iframe src="https://drive.google.com/file/d/15Y8Q-OHDhgEhV4rY7L_RVG6gBxOKRb9g/preview" width="50%" height="900" allowfullscreen="allowfullscreen">

</iframe>

## **Projektin lataaminen tietokoneelle QGIS-työpöytäsovellukseen**

Jos haluat tarkastella projektia, lisätä georeferoituja karttoja ja muokkailla tallentamiasi tietoja tietokoneella toimi seuraavasti:

### **QGIS:n lataaminen ja asentaminen**

Mene QGIS:n viralliselle sivulle: <https://qgis.org/>

Valitse ***Download Now*** ja lataa versio:

![](img/projektin_lataaminen_qgisiin/img1.png){width="261"}

käyttöjärjestelmällesi (Windows, Mac, Linux).

Asenna QGIS seuraamalla asennusohjeita.

### **MerginMaps-lisäosan asentaminen QGISiin**

1.  Avaa QGIS

2.  Valitse ylävalikosta ***Lisäosat → Hallinnoi ja asenna lisäosia*****.**

3.  Kirjoita hakukenttään ***Mergin*****.**

4.  Valitse ***Mergin Maps*** ja klikkaa ***Asenna lisäosa*****.**

![](img/projektin_lataaminen_qgisiin/img2.png)

Kun asennus on valmis, lisäosa löytyy QGIS:n selain ikkunasta, jonka otsikko on *Mergin Maps*.

**Kirjautuminen MerginMaps-lisäosaan**

Avaa lisäosa valikosta: ***Lisäosat → Mergin Maps → Configure MerginMaps plugin*** -ikonista.

![](img/projektin_lataaminen_qgisiin/img3.png)

Tämän jälkeen ohjelma pyytää asettamaan uuden päätodennussalasanan QGISiin. Anna siihen haluamasi salasana ja laita se talteen.

![](img/projektin_lataaminen_qgisiin/img4.png)

Kirjaudu sisään Mergin-tililläsi.

Valitse **Save credentials***,* jos haluat että ohjelma muistaa tunnuksesi seuraavilla kerroilla.

![](img/projektin_lataaminen_qgisiin/img5.png)

Kun kirjaudut, lisäosa yhdistyy Mergin-tiliisi, ja voit nähdä projektisi listattuna.

**Projektin lataaminen QGIS:iin MerginMaps-lisäosalla**

1.  Avaa ***Mergin Maps*** -paneeli QGIS:ssä vasemman laidan selainosiosta.

2.  Paneelissa näet kaikki projektisi.

3.  Valitse projekti, jonka haluat ladata.

4.  Klikkaa ***Download*** ***projec**t* (Lataa projekti).

5.  Valitse kansio, johon projekti tallennetaan. Laita mieleen tämä sijainti. Tähän samaan sijaintiin tallennetaan myöhemmin [georeferoidut kuvat](https://gispocoding.github.io/eip-peltomappi/salaojakarttojen_georeferointi.html).

6.  QGIS avaa projektin ja siihen liittyvät aineistot automaattisesti.

![](img/projektin_lataaminen_qgisiin/mergin_maps_projektin_lataus.gif)
