# COSMIC ROGUELIKE v5.0

Un shooter espacial estilo roguelike de ritmo rápido desarrollado en Python con Pygame. Enfréntate a enjambres orgánicos, drones mineros y jefes titánicos mientras navegas por un universo dinámico lleno de peligros gravitacionales y fenómenos cósmicos.

## Características Destacadas

### 1. Mecánicas de Combate Avanzadas
- **Sistema de Hackeo (HACK):** Detén el tiempo para los proyectiles enemigos, cámbiales el color y redirígelos hacia tus oponentes en un contraataque masivo.
- **Bullet Time:** Cuando tu salud cae por debajo del 10%, el tiempo se ralentiza automáticamente para darte una última oportunidad de esquivar y sobrevivir.
- **Guerra de Facciones:** Observa (o interviene) en batallas entre el "Enjambre Orgánico" y los "Drones Mineros". Aliarte implícitamente con una facción puede otorgarte buffs temporales.

### 2. Progresión y Meta-progression
- **Nexo de Datos:** Recolecta "Fragmentos de Datos" durante tus partidas para desbloquear mejoras permanentes (Sinergias) y descubrir el lore oculto de los sectores galácticos.
- **Eco-Evolución:** Los enemigos no se quedan atrás. El sistema de IA analiza tus tácticas y evoluciona las defensas y ataques de los enemigos para contrarrestar tu estilo de juego.

### 3. Entorno Dinámico
- **Física Gravitacional:** Interactúa con agujeros negros que alteran tu trayectoria y nebulosas densas que afectan tus sistemas de radar y propulsión.
- **Iluminación Deferida:** Un sistema de renderizado que gestiona múltiples fuentes de luz (motores, disparos, explosiones) para una atmósfera inmersiva.
- **IA de Nave Sarcástica:** Tu computadora de a bordo tiene personalidad propia, comentando (a menudo con sarcasmo) sobre tu desempeño, rachas de bajas y errores tácticos.

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Motor Gráfico:** [Pygame](https://www.pygame.org/)
- **Matemáticas:** NumPy (para cálculos de ruido Perlin y vectores)
- **Estructuras de Datos:** Quadtree (para optimización de colisiones en mundos masivos)

## Instalación y Ejecución

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/cosmic-roguelike.git](https://github.com/tu-usuario/cosmic-roguelike.git)
   cd cosmic-roguelike
   
2. **Instala las dependencias**
   ```bash
   pip install pygame
   pip install numpy

3. **Ejecuta el juego**
   ```bash
   python rogue2.0.py

## **Controles**
- **WASD / Flechas: Movimiento de la nave.**

- **Mouse: Apuntar y Disparar.**

- **[E]: Activar Sistema de Hack (EMP).**

- **[Shift]: Turbo / Sobredrive.**

- **[Esc]: Menú / Pausa / Nexo de Datos.**

### **Estructura del Proyecto**

- **rogue2.0.py**: El núcleo del juego que contiene los sistemas de renderizado, física e IA.

- **nexus_data.json**: Archivo de persistencia para tus fragmentos y sinergias desbloqueadas.

- **ghost_run.json**: Almacena datos de tus mejores partidas.

Desarrollado con ❤️ por **Andres Carrillo/AndresCarrillo444**
