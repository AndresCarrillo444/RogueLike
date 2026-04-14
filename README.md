# Cosmic Roguelike Engine

Este proyecto es un motor de videojuego estilo Roguelike de disparos espaciales desarrollado íntegramente en Python. El desarrollo se centra en la implementación de patrones de diseño para sistemas de juego, gestión eficiente de entidades y una arquitectura de estados robusta.

## Especificaciones Técnicas

El núcleo del juego utiliza una combinación de programación orientada a objetos (OOP) y procesamiento vectorial:

- **Motor de Renderizado:** Basado en `pygame` con soporte para múltiples capas de dibujo.
- **Cálculo Matemático:** Uso de `numpy` para operaciones de vectores, trayectorias de proyectiles y lógica de movimiento inercial.
- **Persistencia de Datos:** Sistema de guardado y carga mediante archivos `JSON` para el progreso del árbol de habilidades y configuraciones.

## Arquitectura del Proyecto

El código fuente en `Roguelike.py` se estructura bajo los siguientes pilares:

### 1. Sistema de Entidades y Combate
- **AlliedFleet & EnemyManager:** Controladores dedicados para el ciclo de vida de las entidades, optimizando la detección de colisiones y el filtrado de objetos fuera de pantalla.
- **Lógica de Proyectiles:** Implementación de diferentes tipos de daño, incluyendo efectos de área, rayos Tesla y proyectiles con aceleración variable.
- **Particle System:** Sistema de partículas basado en tiempo de vida (TTL) para explosiones, estelas de motores y efectos visuales de impacto.

### 2. Gestión de Estados (Game States)
El juego utiliza una máquina de estados para separar la lógica de ejecución:
- `GameState.WARP`: Transiciones animadas entre niveles.
- `GameState.PLAYING`: Bucle principal de combate y físicas.
- `GameState.PRACTICE`: Entorno de pruebas con configuración dinámica de oleadas y puntos de habilidad ilimitados.

### 3. Sistema de Progresión
- **Skill Tree:** Implementación de un árbol de habilidades que modifica las constantes del jugador (velocidad, cadencia de tiro, escudos) en tiempo real.
- **Nexus Synergies:** Lógica de combinación de habilidades que desbloquea beneficios pasivos cuando se cumplen ciertos requisitos de nivel.

## Instalación

1. Asegúrate de tener Python 3.8 o superior instalado.
2. Clona este repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/nombre-del-repo.git](https://github.com/tu-usuario/nombre-del-repo.git)
3. Instala las librerías necesarias:
   ```bash
   pip install pygame numpy
## Uso y Controles
Ejecución: python Roguelike.py

Movimiento: Teclas W, A, S, D o flechas de dirección.

Disparo: Espacio o Click izquierdo.

Interacción: Tecla X para acceder al nexo o mejorar habilidades.

## Detalles de Desarrollo
Este repositorio demuestra buenas prácticas de desarrollo backend aplicadas a videojuegos:

Modularidad: Separación clara entre la lógica de datos (dataclasses) y la lógica de representación.

Optimización: Uso de métodos abstractos (ABC) para definir comportamientos base en los sistemas de juego.

Escalabilidad: El WaveManager permite añadir nuevos tipos de enemigos y patrones de ataque simplemente extendiendo las configuraciones existentes.

#### Desarrollado con un enfoque en clean code y arquitecturas de software eficientes.
