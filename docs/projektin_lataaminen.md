# **Projektin lataaminen**

## **Projektin lataaminen mobiilisovellukseen sähköpostilinkin avulla**

Kun olet liittynyt uudeksi testaajaksi [lomakkeen avulla](https://forms.gle/53ukXLJhRCDZmWAF9), saat sähköpostiisi seuraavien päivien aikana linkin:
<img src="img/projektin_lataaminen_qgisiin/sahkoposti_linkki.jpg" width="34%"/>

!!! note "**💡 HUOM!**" 
    Tarkista roskapostikansiosi, jos vahvistussähköposti ei näy postilaatikossasi.

1.  Klikkaa linkkiä ja rekisteröidy palveluun:

<img src="img/projektin_lataaminen_qgisiin/rekisteroityminen.jpg" width="34%"/><br>
2.  Liity työtilaan napauttamalla "Join workspace"

<img src="img/projektin_lataaminen_qgisiin/tyotilaan_liittyminen.jpg" width="34%"/><br>
3.  Avaa tämän jälkeen MerginMaps -sovellus puhelimessasi ja napauta oikean yläkulman ikonia:

<img src="img/aloitusnakyma.jpg" width="34%"/><br>
4.  Kirjaudu tämän jälkeen juuri luomillasi tunnuksillasi sisään:

<img src="img/kirjautuminen.jpg" width="34%"/><br>
5. Napauta tämän jälkeen alareunan ***Projektit***- kohtaa ja lataa eip-peltomappi- projekti

<iframe src="https://drive.google.com/file/d/15Y8Q-OHDhgEhV4rY7L_RVG6gBxOKRb9g/preview" width="50%" height="900" allowfullscreen="allowfullscreen">

</iframe>

## **Uusimman projektitiedoston lataaminen mobiilisovellukseen (vanhat testaajat)**

1. Avaa Mergin Maps- mobiilisovellus

2. Valitse alavalikosta ***Projektit*** ja napauta eip-peltomappi- projektia

3. Lataa projekti, jonka jälkeen projekti on käytössäsi.

<iframe src="https://drive.google.com/file/d/1QnAaKbqdkA8rmEdjK6DCJKP0BYCil74b/preview" width="50%" height="900" allowfullscreen="allowfullscreen">

## **Projektin lataaminen tietokoneelle QGIS-työpöytäsovellukseen**

!!! note "💡 **Info**" 
    **Mergin Maps mobiilisovelluksen käyttö ei edellytä QGISin käyttöä**. Sitä voi käyttää täysin itsenäisesti, mutta jos haluat laajemmat työkalut käyttöön ja haluat tarkastella projektia, lisätä georeferoituja karttoja ja muokkailla tallentamiasi tietoja tietokoneella ne onnistuvat parhaiten QGISin avulla.

!!! note "💡 **Info**" 
    QGIS on avoimen lähdekoodin paikkatieto-ohjelmisto, jonka avulla voit tarkastella, muokata ja analysoida paikkatietoaineistoja. Kun lataat projektin QGISiin, näet peltolohkosi kartalla ja voit käsitellä niihin liittyviä ominaisuustietoja myös ilman verkkoyhteyttä. 
    

    
### **QGIS:n lataaminen ja asentaminen**

Mene QGISin viralliselle sivulle: <https://qgis.org/>

Valitse ***Download Now*** ja lataa versio käyttöjärjestelmällesi (Windows, Mac, Linux):

<img src="img/projektin_lataaminen_qgisiin/img1.png" width="79%"/>

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

**Projektin lataaminen QGISiin MerginMaps-lisäosalla**

1.  Avaa ***Mergin Maps*** -paneeli QGIS:ssä vasemman laidan selainosiosta.

2.  Paneelissa näet kaikki projektisi.

3.  Valitse projekti, jonka haluat ladata.

4.  Klikkaa ***Download*** ***project*** (Lataa projekti).

5.  Valitse kansio, johon projekti tallennetaan. Laita mieleen tämä sijainti. Tähän samaan sijaintiin tallennetaan myöhemmin [georeferoidut kuvat](https://gispocoding.github.io/eip-peltomappi/salaojakarttojen_georeferointi.html).

6.  QGIS avaa projektin ja siihen liittyvät aineistot automaattisesti.

![](img/projektin_lataaminen_qgisiin/mergin_maps_projektin_lataus.gif)
