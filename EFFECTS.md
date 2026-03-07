# Effects Guide

Detailed descriptions of all 19 procedural lighting effects. Every effect runs indefinitely, never repeating the same pattern twice. Each has a companion `_config.py` file that can be edited while the effect is running for instant hot-reload.

---

## Arc Sweep

**File:** `effects/arc_sweep.py` | **FPS:** 20

Arcs of light sweep across the keyboard from random directions. Each arc has a bright green center that fades to dark magenta at the edges, followed by a teal trail that dims as it passes. Multiple arcs can overlap, creating layered washes of color. The speed and pause between sweeps are randomized, and per-row column offsets give the wavefront a curved shape.

**Palette:** Bright green center, dark magenta edges, teal trailing fade.

**Key config parameters:**
- `SPEED_MIN` / `SPEED_MAX` — sweep speed range
- `PAUSE_MIN` / `PAUSE_MAX` — delay between sweeps
- `ROW_OFFSETS` — per-row offsets that shape the arc curvature

---

## Lightning Strike

**File:** `effects/lightning_strike.py` | **FPS:** 15

Procedural lightning bolts strike from the top of the keyboard to the bottom with realistic zigzag paths. Each bolt has a bright white core, purple branches that fork off at random rows, and a chance of restrikes and teal surge flickers. Multi-bolt storms can fire 2-3 bolts in quick succession. The timing mimics natural thunderstorm rhythm with randomized pauses between events.

**Palette:** White bolt core, purple branches, ice blue branch fade, teal surge, dark navy ambient glow.

**Key config parameters:**
- `INTERVAL_MIN` / `INTERVAL_MAX` — seconds between strikes
- `MULTI_BOLT_CHANCE` — chance of rapid successive bolts
- `BRANCH_CHANCE` — probability of branches at each row
- `RESTRIKE_CHANCE` — chance of a re-flash after the initial bolt
- `SURGE_CHANCE` — chance of a teal flicker after restrike

---

## Binary Cascade

**File:** `effects/binary_cascade.py` | **FPS:** 18

Matrix-style falling streams of green light. Each stream has a bright white head followed by a gradient trail from bright green through mid green to a dim green tail. Random cyan glints sparkle through the streams. Streams spawn independently across columns at varying speeds and trail lengths, creating a constant rain of digital characters.

**Palette:** White head, bright/mid/dim green trail, cyan glints, dark green background glow.

**Key config parameters:**
- `STREAM_SPAWN_CHANCE` — per-column per-frame spawn probability
- `MAX_STREAMS` — maximum simultaneous streams
- `SPEED_MIN` / `SPEED_MAX` — fall speed in cells per frame
- `TRAIL_LENGTH_MIN` / `TRAIL_LENGTH_MAX` — trail length range
- `GLINT_CHANCE` — probability of cyan sparkle per visible cell

---

## Tidal Swell

**File:** `effects/tidal_swell.py` | **FPS:** 20

Ocean waves roll horizontally across the keyboard with realistic depth shading. The wave body transitions from deep ocean blues at the trough to bright green crests, topped with white-green foam and occasional white spray highlights. A secondary wave at a different frequency can overlay the primary wave for more complex motion. A slow vertical swell gives the whole scene a gentle breathing rhythm.

**Palette:** Deep ocean blue, trough blue-teal, green wave body, bright green crest, white-green foam, white spray.

**Key config parameters:**
- `WAVE_SPEED` — horizontal scroll speed
- `WAVE_COUNT` — number of wave crests across the keyboard
- `SWELL_SPEED` — vertical breathing speed
- `FOAM_CHANCE` — probability of foam sparkle at wave crests
- `SECONDARY_WAVE` — enable/disable overlay wave

---

## Plasma

**File:** `effects/plasma.py` | **FPS:** 20

Classic demoscene plasma effect with layered sine waves at different frequencies and angles. Multiple sine functions combine to create organic, flowing color fields that drift across the keyboard. An optional second plasma layer with different parameters blends on top for added visual complexity. The orange-purple palette creates a warm, psychedelic atmosphere.

**Palette:** Deep orange through vivid lavender to deep purple (symmetric gradient).

**Key config parameters:**
- `SCALE_X` / `SCALE_Y` — spatial frequency of the plasma
- `TIME_SPEED` — animation speed in radians per frame
- `OVERLAY` — enable second plasma layer
- `OVERLAY_BLEND` — blend weight of the overlay (0 = none, 1 = full)

---

## Searchlight

**File:** `effects/searchlight.py` | **FPS:** 20

A rotating beam of light sweeps across a deep purple background, like a lighthouse or searchlight. The beam has a warm white/yellow core that fades through a warm glow to a green-tinted edge. Subtle brightness flicker adds realism. The beam origin and width are configurable, and the purple ambient background gives the whole keyboard a moody base tone.

**Palette:** Deep purple background, warm white/yellow core, warm glow mid, green-tinted edge.

**Key config parameters:**
- `SWEEP_SPEED` — rotation speed in radians per frame
- `BEAM_WIDTH` — angular width of the beam
- `BEAM_FALLOFF` — edge sharpness (higher = sharper cutoff)
- `ORIGIN_X` / `ORIGIN_Y` — beam pivot point
- `FLICKER` / `FLICKER_AMOUNT` — subtle brightness variation

---

## Glitch

**File:** `effects/glitch.py` | **FPS:** 15

Alternates between a quiet dim-green baseline and violent glitch bursts. During bursts, random keys flash with bright green, hot pink, red, white, and cyan. Row-shift corruption displaces entire rows sideways, and bright horizontal scanlines cut across the display. Multi-burst chains can fire in rapid succession. The timing between bursts is randomized, creating a tense, unpredictable rhythm.

**Palette:** Dim green idle, with bursts of bright green, hot pink, red, white, and cyan.

**Key config parameters:**
- `IDLE_MIN` / `IDLE_MAX` — seconds between glitch bursts
- `BURST_FRAMES_MIN` / `BURST_FRAMES_MAX` — burst duration
- `BURST_DENSITY_MIN` / `BURST_DENSITY_MAX` — fraction of keys affected
- `CORRUPTION_CHANCE` — probability of row-shift per frame
- `SCANLINE_CHANCE` — probability of bright scanline per frame
- `MULTI_BURST_CHANCE` — chance of rapid successive bursts

---

## Fractal Zoom

**File:** `effects/fractal_zoom.py` | **FPS:** 15

Continuously zooms into a Mandelbrot or Julia set fractal, rendered in a purple nebula palette. The view slowly rotates as it zooms, revealing new detail at each level. A breathing pulse modulates brightness for added life. When the zoom reaches its limit, it resets and begins again from a new perspective. Supports switching between Mandelbrot and Julia modes via config.

**Palette:** Near-black purple through deep purple to vivid magenta (symmetric nebula gradient).

**Key config parameters:**
- `ZOOM_SPEED` — zoom progression per frame
- `ZOOM_RANGE` — total zoom depth before reset
- `ROTATION_SPEED` — slow rotation in radians per frame
- `MAX_ITER` — iteration depth (detail vs. performance)
- `JULIA_MODE` — switch between Mandelbrot and Julia sets
- `PULSE` / `PULSE_SPEED` — breathing brightness modulation

---

## Lissajous

**File:** `effects/lissajous.py` | **FPS:** 24

A bright dot traces Lissajous curves across the keyboard, leaving a fading green trail behind it. The curve shape morphs over time as frequencies and phase shift gradually, so the pattern never settles into a static loop. A soft glow surrounds the dot head. Periodically, the frequencies jump to new values for fresh shapes.

**Palette:** Dark background, white dot head, green trail fading to dim green, green glow.

**Key config parameters:**
- `FREQ_X` / `FREQ_Y` — Lissajous frequency ratio
- `PHASE_SPEED` — phase shift speed (controls shape morphing)
- `ANIM_SPEED` — dot travel speed along the curve
- `TRAIL_LENGTH` — number of trailing dots
- `GLOW_RADIUS` — radius of glow around the dot
- `MORPH` / `MORPH_INTERVAL` — periodic frequency randomization

---

## Heat Diffusion

**File:** `effects/heat_diffusion.py` | **FPS:** 20

A thermal simulation where random hot spots ignite across the keyboard. Heat spreads to neighboring cells via discrete Laplacian diffusion while the entire grid slowly cools. The result is mapped to a hot iron palette that transitions from black through red and orange to yellow and white. Hot spots flare up, spread warmth to their surroundings, and gradually fade as cooling wins out — creating a constantly shifting thermal landscape.

**Palette:** Black → dark red → orange → yellow → white (hot iron).

**Key config parameters:**
- `DIFFUSION_RATE` — heat spread speed (0.25 = stable diffusion)
- `COOLING` — global cooling per frame
- `IGNITION_CHANCE` — probability of a cell igniting per frame
- `IGNITION_HEAT` — temperature of new ignitions

---

## Metaballs

**File:** `effects/metaballs.py` | **FPS:** 24

Molten lava blobs drift on Lissajous paths across the keyboard. Each blob generates a scalar field (radius²/distance²), and where fields overlap the blobs appear to merge organically. The field value is mapped through a lava palette: dark edges glow red, the fringe turns orange, and merged cores blaze yellow-white. Aspect ratio correction accounts for non-square key spacing.

**Palette:** Black → dark red → red-orange → orange → yellow → yellow-white (molten lava).

**Key config parameters:**
- `NUM_BLOBS` — number of metaballs (up to 5)
- `BLOB_RADIUS` — radius affecting field strength
- `SPEED` — blob movement speed
- `ASPECT_RATIO` — horizontal/vertical key spacing ratio
- `THRESHOLD` — field value at the blob "surface"

---

## Chladni Patterns

**File:** `effects/chladni.py` | **FPS:** 20

Visualizes the nodal lines of a vibrating plate — the Chladni figures from acoustics. The formula `a·sin(πnx)·sin(πmy) + b·sin(πmx)·sin(πny)` is evaluated across the keyboard, and brightness peaks at the nodal lines where the amplitude passes through zero. The effect crossfades between different mode pairs (n, m) over time, morphing from one geometric pattern to another. A gentle breathing pulse keeps the pattern alive.

**Palette:** Dark navy background, bright azure/cyan nodal lines.

**Key config parameters:**
- `NODAL_WIDTH` — width of the bright nodal lines (Gaussian spread)
- `MORPH_SPEED` — crossfade speed between mode pairs
- `PULSE_SPEED` — breathing pulse frequency
- `MODE_PAIRS` — list of (n, m) mode pairs to cycle through

---

## Cyclic Cellular Automaton

**File:** `effects/cyclic_cellular.py` | **FPS:** 12

A grid of cells cycles through 14 states. Each step, a cell advances to the next state if any of its 8 neighbors (Moore neighborhood) already holds that successor state. Starting from random noise, this simple rule produces emergent rotating spirals and traveling waves in a full rainbow palette. The grid wraps toroidally. If the automaton stagnates (no cells change), it automatically re-seeds with fresh random noise.

**Palette:** 14-color rainbow generated from HSV (one hue per state, evenly spaced).

**Key config parameters:**
- `NUM_STATES` — number of states in the cycle (changes palette size)
- `THRESHOLD` — minimum neighbors required to advance
- `SIM_STEPS_PER_FRAME` — simulation steps per rendered frame
- `STAGNATION_FRAMES` — frames without change before re-seed

---

## Magnetic Field Lines

**File:** `effects/magnetic_field.py` | **FPS:** 20

Four magnetic poles (alternating positive and negative charges) drift across the keyboard on Lissajous paths. At each pixel, the total magnetic field vector is computed from all poles, then visualized as an iron filings pattern: brightness follows `|sin(N·angle)| × magnitude`, creating the characteristic line patterns that reveal field topology. Positive poles glow red and negative poles glow blue. When poles pass close to each other, the field topology snaps dramatically.

**Palette:** Dark background, cyan field lines, red positive pole glow, blue negative pole glow.

**Key config parameters:**
- `NUM_POLES` — number of magnetic poles
- `POLE_SPEED` — drift speed of poles
- `NUM_LINES` — number of field line bands (controls pattern density)
- `FIELD_SCALE` — brightness scaling of field magnitude
- `POLE_GLOW_RADIUS` / `POLE_GLOW_INTENSITY` — pole proximity glow

---

## Wave Interference

**File:** `effects/wave_interference.py` | **FPS:** 24

A 2D wave equation simulation with 3 moving point sources emitting sine waves. Waves propagate across the grid using Verlet integration, reflecting off boundaries and interfering constructively and destructively. Damping prevents amplitude overflow. Sources drift on Lissajous-like paths, continuously changing the interference pattern. The diverging palette maps negative amplitudes to blue, zero to black, and positive amplitudes to gold.

**Palette:** Blue (negative) → black (zero) → gold (positive), diverging.

**Key config parameters:**
- `SPEED` — wave propagation speed
- `DAMPING` — amplitude damping per step (prevents blowup)
- `AMPLITUDE` — source injection strength
- `NUM_SOURCES` — number of emitting point sources
- `WAVE_FREQ` — emission frequency
- `SOURCE_SPEED` — how fast sources drift across the grid

---

## Fireflies

**File:** `effects/fireflies.py` | **FPS:** 20

Each key is an independent oscillator with its own natural frequency, coupled to its neighbors via the Kuramoto model. The coupling strength oscillates slowly over time, causing the system to cycle between synchronized flashing (all keys fire together) and chaotic independent blinking. Each oscillator's brightness is a sharp flash — `max(0, sin(phase))^sharpness` — mimicking the brief blink of a firefly. The palette transitions from dark green through yellow-green to a bright white flash at peak.

**Palette:** Dark green (dim) → yellow-green (mid) → bright yellow-green → white (flash peak).

**Key config parameters:**
- `MEAN_FREQ` — average oscillation frequency
- `FREQ_SPREAD` — variation in natural frequencies
- `COUPLING` — maximum coupling strength (K)
- `COUPLING_SPEED` — how fast coupling oscillates (sync/chaos cycle rate)
- `FLASH_SHARPNESS` — exponent controlling flash brevity (higher = sharper)

---

## Crystal Growth

**File:** `effects/crystal_growth.py` | **FPS:** 12

Diffusion-Limited Aggregation (DLA) grows a crystal from a single seed at the center of the keyboard. Random walkers spawn from the edges and drift randomly; when one touches the crystal (8-connected), it sticks and becomes part of the structure. Growth is capped to one attachment per frame for visible progression. Each cell is colored by its attachment order through a blue-teal-green-amber-red palette, with a brief white flash when it first attaches. When the crystal exceeds 55% fill, it resets and grows anew.

**Palette:** Blue (early growth) → teal → green → amber → red (late growth), with white flash on attachment.

**Key config parameters:**
- `MAX_WALKERS` — number of active random walkers
- `WALK_STEPS` — random walk steps simulated per frame
- `MAX_ATTACH_PER_FRAME` — cap on new crystal cells per frame
- `FILL_THRESHOLD` — fraction of grid filled before reset
- `FLASH_FRAMES` — duration of white flash on new attachment

---

## Reaction-Diffusion

**File:** `effects/reaction_diffusion.py` | **FPS:** 20

Two chemicals (A and B) interact via the Gray-Scott reaction-diffusion equations, producing organic cell-like patterns that split, pulse, and reform endlessly. Chemical A fills the grid while B is seeded in small patches. The reaction `A + 2B → 3B` creates autocatalytic growth, balanced by feed and kill rates. A weighted 9-point Laplacian with toroidal wrapping handles diffusion. The mitosis parameter set (f=0.0367, k=0.0649) produces self-replicating spots. Chemical B concentration maps to a bioluminescent teal-cyan palette. If B dies out, the system re-seeds automatically.

**Palette:** Black → dark teal → teal → bright cyan-teal → cyan-white (bioluminescent).

**Key config parameters:**
- `FEED` — feed rate of chemical A (controls pattern type)
- `KILL` — kill rate of chemical B (controls pattern type)
- `D_A` / `D_B` — diffusion rates (B diffuses slower than A)
- `SIM_STEPS` — simulation iterations per rendered frame
- `RESEED_THRESHOLD` — minimum B sum before automatic re-seed

---

## Physarum

**File:** `effects/physarum.py` | **FPS:** 20

A slime mold (Physarum polycephalum) simulation. 150 agents wander a high-resolution internal buffer (2x the keyboard resolution), each with three forward-facing sensors. Agents sense the trail map ahead and steer toward higher concentrations, depositing their own trail as they move. The trail map diffuses (3x3 box blur) and decays each frame. This creates self-organizing vein-like transport networks that form, merge, and dissolve organically. The buffer is downsampled to keyboard resolution for display.

**Palette:** Black → dark green → olive-green → bright yellow-green → bright yellow → pale yellow (bioluminescent).

**Key config parameters:**
- `NUM_AGENTS` — number of slime mold agents
- `SENSOR_ANGLE` — angle between sensors (radians)
- `SENSOR_DIST` — how far ahead agents sense
- `TURN_SPEED` — steering rate (radians per step)
- `DEPOSIT_AMOUNT` — trail deposited per step
- `DECAY_RATE` — trail decay multiplier per frame
- `BUFFER_SCALE` — internal buffer resolution multiplier
