# Bomber: La Nueva Era

Marcador de las partidas de Bomberman entre Sergio, Joel, Gonzalo y Parce.
Una partida ganada = un punto.

Todo vive en un solo archivo: `index.html`. Se abre con doble clic o desde
GitHub Pages: https://jarbit8.github.io/bomber/

## Que trae

- Intro animada: tablero de bloques, bomba con mecha, cuenta regresiva y explosion en cruz.
- Pestana **GLOBAL**: podio, ranking con barras, partidas jugadas y efectividad.
- Pestana **POR DIAS**: cada jornada con su fecha, quienes jugaron y los puntos de cada uno.
  Los `+` y `-` de cada jornada actualizan el global al instante.
- Respaldo local en el navegador, mas botones de exportar/importar JSON.

## Sincronizar entre todos (Firebase)

Sin esto, cada quien ve solo lo que anoto en su propio equipo. Faltan dos pasos
en la consola de Firebase del proyecto `bomber-3a196`:

**1. La clave.** Configuracion del proyecto -> General -> "Clave de API web".
Pegarla en `index.html`, en la linea:

```js
const API_KEY = '';
```

**2. Las reglas.** Realtime Database -> Reglas:

```json
{
  "rules": {
    "nuevaEra": {
      ".read": true,
      ".write": "auth != null && auth.token.email === 'jarb2299@gmail.com'"
    }
  }
}
```

Asi cualquiera puede mirar el marcador, pero solo jarb2299@gmail.com puede
anotar puntos (entrando con el boton "ENTRAR PARA EDITAR").

Ademas, en Authentication:
- Activar el proveedor **Google**.
- En "Dominios autorizados" agregar `jarbit8.github.io`.
