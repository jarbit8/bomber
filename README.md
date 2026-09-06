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

**2. El login por PIN.** En vez de una cuenta de Google, es una sola cuenta de
Firebase (correo + contrasena) donde la "contrasena" es el PIN. Asi desde
cualquier compu solo se escribe el PIN, sin iniciar sesion con nada.

En Authentication -> Sign-in method: activar el proveedor **Email/Password**.

En Authentication -> Users -> "Add user":
- Correo: `pin@bomber-nueva-era.local` (tiene que ser EXACTO, asi lo busca el codigo)
- Contrasena: el PIN elegido (minimo 6 caracteres, puede ser solo numeros)

**3. Las reglas.** Realtime Database -> Reglas:

```json
{
  "rules": {
    "nuevaEra": {
      ".read": true,
      ".write": "auth != null && auth.token.email === 'pin@bomber-nueva-era.local'"
    }
  }
}
```

Asi cualquiera puede mirar el marcador, pero solo quien sepa el PIN puede
anotar puntos (metiendolo en la cajita de abajo del todo).

Para cambiar el PIN mas adelante: Authentication -> Users -> los tres puntos
del usuario `pin@bomber-nueva-era.local` -> "Reset password", o borrarlo y
crearlo de nuevo con otra contrasena.
