# Madrid Pulse · Interacción y revisión visual

Referencias de diseño propias: [prototipo](live.html), [vista general](01-escritorio.png), [móvil](02-movil.png), [seguimiento sin señal reciente](03-tren-sin-senal.png), [Explore](04-explore.png). Los mapas son esquemas ilustrativos de C4 y C5, los horarios son ficticios y el instante mostrado es de demostración. La red de producción se construye con los datos y trazados verificados de Madrid.

## Recorrido de dos minutos

1. Abre Live en Atocha. Comprueba origen de la ETA y pausa la cinta inferior.
2. Escribe «alcorcon» y pulsa Intro. Selecciona la salida hacia Humanes. Pulsa «Seguir tren». El plano enfoca la circulación.
3. En «Simular señal» cambia entre GPS, interpolación, estimación, obsoleta y sin conexión. En obsoleta/sin conexión la posición queda congelada. Al arrastrar el fondo del mapa se cancela el seguimiento.
4. Abre el historial desde la ficha y vuelve al mismo tren. En Explore elige C5 para ver el numerador, el denominador y la cobertura del ejemplo.
5. En móvil usa «Ampliar panel» para leer el itinerario. Con teclado puedes seleccionar estación y tren; Escape cierra la búsqueda. El informador admite pausa y el modo de movimiento reducido evita la animación automática.

## Qué tomar de la maqueta para producción

| Elemento | Respuesta esperada | Prueba de aceptación |
|---|---|---|
| Inicio y cámara | Abrir el mapa con destinos y tiempos en primer plano. Respetar el encuadre que el usuario elija | Hacer zoom, esperar dos actualizaciones y comprobar que el mapa no vuelve al centro. «Centrar» responde una sola vez por pulsación. |
| Estaciones y filtros | Búsqueda con y sin tilde, resultados de teclado, ficha compartida en intercambiadores. En producción, selección múltiple de líneas y URL restaurable | Buscar Alcorcón y Atocha. Filtrar líneas C4 y C5 simultáneamente y comprobar que los contadores tienen el mismo ámbito que el mapa. La maqueta incorpora un filtro sencillo para evaluar la interacción. |
| Tablero | Destino, hora prevista, diferencia con horario, cambios de andén cuando existan, procedencia y edad | Probar ETA desconocida, retraso cero, parada omitida y cancelación. Diferenciar «sin salidas registradas» de «fuente sin conexión». |
| Movimiento | Dos anclas confirmadas permiten interpolar en replay o con retraso de reproducción. En directo, avanzar desde una ancla es una proyección y se etiqueta como tal. Solo mover sobre un patrón validado | Dos observaciones, parada en estación, salto entre ramales y degradación de señal. Nunca generar un hecho GPS a partir de un frame. |
| Símbolos y accesibilidad | Usar el color para línea, forma/contorno y texto para procedencia. Preservar un marcador de la última lectura si el símbolo está estimado | Probar en escala de grises, con lector y con movimiento reducido. En producción mostrar el timestamp del punto que realmente se dibuja. |
| Seguimiento | Pulsar el tren conserva la ficha y permite seguirlo. El gesto de arrastre devuelve el control de la cámara | Cambiar de trayecto, perder señal, volver al tren y comprobar que no se seleccionó otra circulación del mismo vehículo. |
| Informador | Cambiar entre novedades legibles a velocidad de lectura; cada una abre su tren o estación. Pausa persistente durante la sesión y alternativa estática en producción | Simular dos avisos iguales, uno caducado y uno nuevo; publicar solo el cambio. No anunciar continuamente a lectores de pantalla. |
| Fallos y recuperación | Si falla cartografía o WebGL, el tablero sigue siendo navegable. Un fallo de avisos no borra posiciones; la edad avanza aunque falle el siguiente poll | Cortar solo un feed, luego toda la red, y restaurar. Mantener la última hora buena junto a su estado. El selector del prototipo simula estas condiciones para revisar el diseño. |
| History y Explore | Conservar contexto de viaje o línea. Cálculo de puntualidad sobre los cubiertos y cobertura sobre los elegibles | Volver a Live desde el historial. Para el ejemplo C5: 16 puntuales de 20 cubiertos = 80 %, 20 de 24 programados ≈ 83 % de cobertura. Para datos reales comprobar contra el mart y el contrato del KPI. |

La prueba de MP-020 requiere evidencias del frontend de Madrid Pulse con la API propia. Estas pantallas ayudan a discutir jerarquía visual, navegación y estados antes del desarrollo.
