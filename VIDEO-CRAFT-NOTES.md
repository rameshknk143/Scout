# Video Craft Notes — ScoutVeda Reference Analysis (Updated 2026-09-23)

**Date:** 2026-09-23  
**Source Videos:** 4 reference videos (v1: 3D websites, v2: Apple-style product, v3: Iron Man scrolling UI, v4: GSAP web design course)  
**Total Frames Analyzed:** 35+  
**Vision Model:** agnes-2.5-flash via nararouter API

---

## V3 Frames — Iron Man Scrolling UI (Highest Priority)

### v3_f2.jpg
- **Layout:** Asymmetrical cinematic grid; left two-thirds dominated by oversized typography as visual anchor, right third features photographic subject integrated into space rather than rigid container
- **HUD Elements:** Delicate L-shaped corner brackets (top-left, bottom-left) evoking targeting reticle aesthetic
- **Color Palette:** Deep charcoal/obsidian (#050505), metallic gold/bronze (#D4AF37, #C5A028), warm amber glow (#FFB347), stark white (#FFFFFF), muted grey-gold secondary text (#666666)
- **Typography:** Bold geometric sans-serif (Futura/Proxima Nova style), tight tracking, massive scale difference between white "Build" and gold "Devini", technical monospace for peripheral navigation
- **Depth/Lighting:** Atmospheric fog, gradient fade from center to edges, warm light emanating from subject as primary source

### v3_f8.jpg
- **Layout:** Rule-of-thirds weighted heavily right, subject gazing upward toward typography creates natural eye path from bottom-left to top-right
- **HUD Overlay:** Information floats in negative space ("fog") around subject, peripheral metadata pushed to absolute edges
- **Color Palette:** Void black (#0A0A0A to #1C1C1C), mist grey (#E8E8E8 to #F5F5F5), Stark gold (#D4AF37), arc cyan glow (#00FFFF), ghost white at low opacity
- **Typography:** Bold geometric sans-serif (Montserrat Black/Helvetica Now Display), utilitarian monospace for labels like "FLIGHT LOG — ARCHIVED"
- **Depth/Lighting:** Volumetric atmospheric scattering, rim light on subject edges, high-contrast separation from background

### v3_f15.jpg
- **Layout:** HUD framework with geometric corner brackets, asymmetric balance skewed left-center balanced by typographic block right
- **Color Palette:** Deep void gradients (#050505 to #1a1a1a), Stark industrial yellow/gold (#D4AF37), subtle crimson gradients bleeding from left (#8B0000), desaturated greys (#666666)
- **Typography:** Tech-serif hybrid (Trajan/custom Stark typeface), sharp high-contrast serif implying authority, monospace utility for navigation
- **Depth/Lighting:** Near-black gradient fading into atmospheric fog suggesting vacuum/smoky environment

### v3_f22.jpg
- **Layout:** Centralized modal strategy, pristine white rectangular card floats in viewport middle as distinct content island against dark peripheral environment
- **Color Palette:** Deep matte charcoal (#1e1e1e to #2d2d2d) for chrome, pure white (#ffffff) with cool undertone for card surface, vibrant digital blue (#1a73e8) for primary action button, pastel icy blue (#d3e3fd) for selection state
- **Typography:** Clean geometric sans-serif (Roboto style), medium weight header with increased point size, regular weight list items with tight letter spacing, column headers in lighter weight or small-caps
- **Depth/Lighting:** Soft diffuse drop shadows lift main card off canvas

### v3_f30.jpg
- **Layout:** Masonry grid anchored by vertical navigation rail on far left, central stage dominated by single tall aspect-ratio card, skeleton loading placeholders on right, hybrid global search bar and contextual action bar float above main content
- **Color Palette:** Cool pale off-white (#F2F2F2) canvas, crisp white (#FFFFFF) for nav rail and active card, signature red (#E60023) for high-value actions, deep charcoal (#111111) for primary text
- **Typography:** Clean geometric sans-serif favoring function over decoration, hierarchy driven by size and opacity, bold commanding save button
- **Depth/Lighting:** Neumorphic subtlety rather than hard borders, soft diffuse drop shadows

### v3_f40.jpg
- **Layout:** Dense modular dashboard, persistent left-hand vertical nav rail (~60px wide), slightly wider secondary panel for settings, center-right multi-column grid for generated media, tertiary right rail for asset library
- **Color Palette:** Deepest charcoal (#0a0a0a to #111111), mid-tone elevated panels (#1c1c1c), electric neon lime/cyan accent (#00ffaa, #39ff14), muted slate grays (#333333), crisp white (#ffffff) fading to soft silver (#aaaaaa)
- **Typography:** Clean geometric sans-serif (Inter/Satoshi), heavy weight variation for hierarchy, compact density maximizing information
- **Depth/Lighting:** Subtle layering via glow effects on active elements, minimal drop shadows, radial gradient on highlighted items

### v3_f50.jpg
- **Layout:** Modular three-pane asymmetric grid optimized for workflow density, slim icon-only left rail, dedicated command center card floating slightly above background, masonry-style grid of results below selected item enlarged, persistent vertical filmstrip sidebar
- **Color Palette:** Deep obsidian/zinc (#09090b to #121215), elevated zinc tones (#18181b, #202023), neon mint/electric green (#00ff9d) for active states, muted slate (#71717a) for secondary text
- **Typography:** Clean functional sans-serif (Inter/Satoshi), heavy bolding reserved strictly for headers, body text medium weight in off-white (#e4e4e7)
- **Depth/Lighting:** Layering through background shifts rather than shadows

### v3_f60.jpg
- **Layout:** Modular three-pane dashboard for parallel workflow, left panel expansive negative space with centered focal point, center panel dedicated entirely to media consumption with cinematic letterbox approach, right panel dense high-information sidebar
- **Color Palette:** Deep void monochromatic base (#050505 left/center, #18181b right sidebar), warm alert orange (#FF6B00) for Claude icon, muted tech-forward green (#10A37F) for ChatGPT branding, pure white fading to dim silver (#888888)
- **Typography:** System-ui sans-serifs mixed with monospaced terminal fonts, clean bold sans-serif for headers, distinct shift to monospace for data/paths
- **Depth/Lighting:** Flat matte aesthetic with subtle border lines creating separation

### v3_f70.jpg
- **Layout:** Strict multi-pane layout reminiscent of professional IDEs, three vertical zones: narrow left sidebar for file navigation, wide central column for primary interaction, right-hand panel for media preview, persistent input bar floats at bottom center, horizontal tab bar at top organizes context
- **Color Palette:** Deep monochromatic midnight scheme (#0d0d0d to #1a1a1a), vibrant warm coral/orange (#ff7f50) for mascot and TODO text, off-white (#e0e0e0) for body text, subtle grays (#2d2d2d) for input fields
- **Typography:** Exclusively monospaced (JetBrains Mono/Fira Code/Source Code Pro variants), compact sizing prioritizing information density, pixel-art logo breaks typographic grid
- **Depth/Lighting:** Radically flat with minimal shadows, subtle border lines and slight background shifts implying depth

### v3_f80.jpg
- **Layout:** Multi-pane asymmetric grid typical of modern developer workstations, compact collapsible file explorer tree, central canvas with generous black space framing logo and prompt input, right overlay media preview panel, sticky header row with tabs and window controls
- **Color Palette:** True black OLED-friendly (#0f0f0f to #000000), high-contrast off-whites (#e5e5e5), muted grays (#666666), singular warm coral/salmon orange (#ff7b5e) for brand mark
- **Typography:** System sans-serif for menus/filenames/buttons, monospace for prompt input area signaling precision/code
- **Depth/Lighting:** Radically flat design with minimal shadows, subtle border lines (#2a2a2a) and slight background shifts creating layering

### v3_f88.jpg
- **Layout:** Centered vertical stack hierarchy balancing text density with generous negative space, flows from top question to direct command CTA, floating action button anchors viewer attention
- **Color Palette:** Deep near-black void (#080808) transitioning to faint atmospheric radial gradient, soft diffuse crimson/magenta halo (#4a0d15) behind text, vivid saturated hot pink/neon red (#ff2a55) for emphasis words like "like" and "SUBSCRIBE!"
- **Typography:** Clean geometric sans-serif (Inter/Helvetica Now), bold legible primary text, heavy weight uppercase tracking for urgency on "SUBSCRIBE!", italicized dynamic energy on "like"
- **Depth/Lighting:** Glow-on-dark aesthetic with vignette edges pitch black drawing center into reddish haze, text appears to emit light via soft outer glow/bloom effect, semi-transparent dark charcoal button floats above background

---

## V1 Frames — 3D Website Visuals

### v1_f2.jpg
- **Layout:** Centralized hero layout, 3D character placed slightly off-center right creating dynamic balance against heavy typographic block left, three distinct visual planes (immersive full-bleed background nebula, 3D foreground character, bold utilitarian text overlay)
- **Color Palette:** Deep nebula indigos/blacks (#0f0c29, #240b36), electric cyan/violet swirls (#4facfe, #a18cd1), hot pink subject (#ff3366), warm walnut brown desk (#6b4c3b), cream keyboard (#f5f5f5)
- **Typography:** Bold utilitarian sans-serif (Montserrat ExtraBold/Impact), pure white uppercase tight tracking, monospaced code snippets (#00ff41 green on dark grey) reinforcing developer tool aesthetic
- **Depth/Lighting:** Volumetric lighting, monitor as light source casting cool blue rim light onto workspace, subsurface scattering on 3D character giving tangible plush volume

### v1_f5.jpg
- **Layout:** Classic centered hero layout, typography left-aligned relative to center sitting heavily in upper-middle third, 3D illustrative anchor below balancing composition, floating pill-shaped top bar navigation
- **Color Palette:** Deep space background gradient (#0B0F1E to #1A1F3C), vibrant purples (#7C3AED) and bright blues (#3B82F6) for buttons/branding, pure white text for maximum readability
- **Typography:** Clean modern geometric sans-serif (Inter/DM Sans), heavy bold weight for impact, relaxed tracking giving text room to breathe
- **Depth/Lighting:** Soft diffuse lighting giving 3D astronaut character tangible plush volume like high-end collectible figure, scattered stars and planetary bodies at different z-depths creating faux-3D environment, subtle bloom/glow around 3D elements

### v1_f8.jpg
- **Layout:** Centered single-column hero structure with breathing room, layered three visual tiers: floating planetary sphere background, primary content stack (logo → headline → input bar → sub-CTA), lower preview panel suggesting dashboard
- **Color Palette:** Deepest void violet (#06061a to #0a0a14), electric violet fading to royal blue (#6B4FE0 to #3B6EF7), hot magenta-pink and cyan edge glow (#C840E8, #4DD9E8), semi-transparent dark panels rgba(12,12,30,0.6) with white/light lavender text
- **Typography:** Clean neo-grotesque sans-serif (Inter/SF Pro), heavy bold ~48–64px for "Sites beyond imagination", lighter weight for "one prompt away", 14–16px body text with comfortable letter-spacing
- **Depth/Lighting:** Cosmic sphere softly lit 3D form with gradient wrap from deep indigo core to glowing violet edge, ambient edge-lighting bloom along bottom in hot pink and top in deep violet, glassmorphic sheen on search bar with faint frosted backdrop, preview card introduces second z-plane floating above cosmic surface

### v1_f11.jpg
- **Layout:** Modern asymmetrical split-screen, left vertical grid of product cards anchoring navigation, right side dominated by negative space allowing large kinetic typography to breathe, translucent pill-shaped nav bar floats at top, glowing horizontal horizon line separates content from footer
- **Color Palette:** Deep obsidian/midnight black (#050505), electric violet/purple (#7B2CBF) for nav, acid teal/cyan (#00E5FF) for glowing horizon line, pops of lime green and bright blue from clothing
- **Typography:** Heavy condensed sans-serif in stark white, large impactful likely utilizing sticky/fixed positioning, all lowercase or mixed giving utilitarian industrial feel
- **Depth/Lighting:** Atmospheric lighting rather than hard shadows, neon cyan light bleed from beneath central content creating light leak effect suggesting reflective surface, blurred white blade-like shape floating in foreground creating parallax depth

### v1_f14.jpg
- **Layout:** Full-bleed dark canvas with center-weighted hero featuring oversized 3D product photography, minimized slim top bar letting product dominate 70%+ viewport, typographic treatment layered behind floating earbuds creating depth-stacked parallax hierarchy
- **Color Palette:** Near-black with whisper blue undertone (#0a0a0c), pure white primary text (#ffffff), secondary muted gray (#8a8a9a), translucent white-grey earbud material (#e8e8ec), faint violet-blue bleed (#6366f1, #818cf8) from screen reflection
- **Typography:** Geometric sans-serif (SF Pro Display/Apple-native), massive 120–140px headline sizing partially occluded by 3D models for depth play, subtle letter-spacing on secondary CTAs
- **Depth/Lighting:** Translucent subsurface scattering on earbuds, light diffuses through silicone tips creating soft inner glow, edge lighting uses rim highlights (#ffffff at ~15% opacity) separating form from dark void, soft directional key light from upper-left casts gentle gradient shading, no harsh shadows everything feels airborne suspended

### v1_f17.jpg
- **Layout:** Minimalist full-bleed dark mode, content anchored upper-left quadrant creating strong visual hierarchy, "screen-within-screen" framing inside MacBook Pro adding physical context and scale
- **Color Palette:** Deep onyx black (#050505 to #0A0A0A), aggressive neon green accent (#00FF41, #39FF14) highlighting word "power", atmospheric violet glow (#7B2CBF) bleeding from screen bezels and laptop chassis
- **Typography:** Bold geometric sans-serif (Inter/Satoshi/Helvetica Now Display), heavy condensed weight authoritative, massive bold headers versus smaller lighter body text, neon green accent breaks white text monotony on strategic word
- **Depth/Lighting:** Cinematic rim lighting, soft ambient RGB glow suggesting monitor setup, atmospheric violet bleed from top/bottom bezels

### v1_f20.jpg
- **Layout:** Cinematic letterbox-style layout, strictly divided two zones: dominant upper void occupying roughly two-thirds canvas, grounding lower section featuring landscape, typography treated as primary structural element stacked asymmetrically upper-left balancing figure lower-right
- **Color Palette:** Deep void black (#050505 to #0A0A0A), electric lime gradient emerging from bottom (#39FF14) acting as light source and horizon line, stark white headlines, technical grey/purple UI elements (#4B0082)
- **Typography:** Brutalist-meets-editorial hierarchy, massive heavy-weight sans-serif ("Helvetica Now/Impact") for "Blow", italicized serif quote (Baskerville/Garamond) for literary weight, clean sans-serif/monospace for HUD numbers ("03", "0.0")
- **Depth/Lighting:** Layered transparency creating ghosting effect, text overlaps 3D element for parallax-like hierarchy without actual scroll movement

---

## V2 Frames — Apple-Style Product Presentation

### v2_f5.jpg
- **Hero Render Treatment:** Headphones rendered as monolithic sculptural form, soft-touch matte polymer with subtle micro-facets avoiding harsh plastic reflectivity, ear cups emerge with volume through controlled edge definition, subsurface scattering hints at leather-bound cushions giving tactile organic warmth beneath industrial exterior
- **Lighting Quality:** Low-key chiaroscuro dominates, single soft directional source sculpts silhouette from above-right grazing outer contour of headband and upper ridge of ear cup, shadows pool deeply into recessed joints creating volumetric depth, no ambient fill lights darkness occupies negative space making illuminated planes feel earned
- **Color Grading:** Near-monochromatic desaturation anchors palette, deep charcoal-black primary canvas, midtone greys establishing dimensionality, highlights lean toward muted silver-cyan temperature clinical yet warm, zero chromatic competition narrative where contrast replaces saturation as language of visual hierarchy
- **Motion Sequencing:** Implied slow hypnotic reveal beginning at macro proximity revealing surface textures and material details before pulling back to establish form

### v2_f90.jpg
- **Hero Render Treatment:** Solitary photorealistic artifact likely smartphone or wearable rendered with sub-pixel precision, materials exhibit subsurface scattering giving glass and silicone lifelike translucency, surface imperfections erased every curve mathematically perfect yet capturing tactile quality of brushed aluminum polished steel or matte ceramic, object feels heavy and substantial anchored by realistic contact shadows
- **Lighting Quality:** Soft volumetric studio lighting creates seamless gradient across form, dominant key light sculpts architecture while rim lights separate silhouette from background tracing edges in cool ethereal glows, specular highlights soft-edged elongated sliding fluidly over curved surfaces emphasizing premium finish
- **Color Grading:** Desaturated sophisticated palette anchoring scene, cool silvers charcoals and muted blues punctuated by warm metallic accents like gold or rose copper, high-contrast yet preserving detail in deepest blacks and brightest highlights avoiding muddy mid-tones, overall tint leans slightly cool reinforcing clinical precision and modern elegance
- **Motion Sequencing:** Slow deliberate orbit revealing product geometry in continuous unbroken take, movements cinematically smooth utilizing parallax to create profound sense of three-dimensional space, transitions between macro detail shots and wider establishing views dissolves so subtle they feel like single breath, pacing unhurried inviting viewer linger on every contour
- **Product-as-Artifact Composition:** Object floats in minimalist void isolated from any environmental context composed like sculptural masterpiece or museum piece

### v2_f180.jpg
- **Hero Render Treatment:** Headphones treated as singular flawless sculpture rather than utilitarian device, geometry hyper-smooth with organic curves suggesting machined aluminum or polycarbonate, ear cups appear to float in void emphasizing ergonomic form factor without distraction of straps or cables, surface simulation key leather headband and ear cushions soft matte diffusion while outer shells exhibit hard-anodized finish rejecting imperfections
- **Lighting Quality:** Low-key dramatic utilizing scrim lighting technique, massive soft key light wraps around left side revealing volume of ear cups while sharp narrow rim light traces silhouette of headband and edge of hinges, controlled specular highlights telling material story cool metal versus warm leather without being distracting
- **Color Grading:** Strictly monochromatic desaturated leaning into stealth luxury aesthetic, background gradient of void black to deep charcoal providing zero chromatic competition, headphones sit in mid-to-dark tone range likely Space Gray or Midnight finish, only pop comes from specular highlights creating high-contrast cinematic look typical of premium tech unveilings
- **Motion Sequencing:** Frame represents hero pass, motion would be slow buttery-smooth orbital dolly around product or subtle push-in z-axis revealing form gradually

### v2_f270.jpg
- **Hero Render Treatment:** Product emerges as hyper-finished digital artifact geometrically pristine with flawless surface continuity and zero visible seams, every curve chamfer and transition mathematically idealized rendered at sub-pixel resolution, physically-based material simulation capturing diffuse roughness and micro-detail reflection simultaneously
- **Lighting Quality:** Studio-grade illumination engineered for emotional weight, soft omnipresent key lights wrap around form without casting hard shadows while precise rim and edge lights carve definition from darkness, specular highlights glide across surfaces like liquid mercury tracing product silhouette in slow motion, subsurface scattering lends warmth and depth to translucent elements
- **Color Grading:** Restrained editorial palette dominates, bone-white voids cool graphite gradients or near-black backgrounds pushing product forward, colors desaturated just enough to feel timeless yet rich where they matter, LUTs lean toward cinematic neutrality preserving only product own color story
- **Motion Sequencing:** Glacial intentional camera movement feathered zooms orbital arcs and tilt transitions feeling like curator rotating museum piece, easing nonlinear accelerations and decelerations mimicking breath rather than mechanics, product may decompose into floating components rotate on invisible axes or reassemble in choreographed sequence

### v2_f360.jpg
- **Hero Render Treatment:** Singular floating icon in void, geometry hyper-perfect no micro-scratches no imperfections, earcups possess heavy substantial volume reminiscent of AirPods Max silhouette but rendered in deeply matte charcoal-finish absorbing light rather than reflecting aggressively, headband curves with mathematical precision suggesting hidden tension spring mechanism
- **Lighting Quality:** Softbox studio aesthetic typical of high-end tech commercials diffuse shadowless in center allowing form to dictate shape, delicate rim lights tracing top contour of earcups and underside of headband separating dark object from dark background, sharp localized specular highlight acts as touch point implying reactivity and premium tactility
- **Color Grading:** Strictly monochromatic desaturated study in Space Gray, blacks crushed but retain depth not pure #000000 creating velvety background, mid-tones cool leaning slightly toward blue-gray enhancing feeling of cold machined aluminum and polished steel, zero color distraction forcing eye entirely onto silhouette and material texture
- **Motion Sequencing:** Implied exploded view transition beginning with stillness of assembled artifact then slowly smoothly disassembling into component parts driver units shock absorbers and aluminum mesh hovering in exploded configuration revealing internal complexity

### v2_f450.jpg
- **Hero Render Treatment:** Composition centers on browser window as primary artifact rendered with cinematic depth of field, background desktop crushed into soft indistinct blur forcing eye exclusively onto sharp high-resolution UI of search interface, window appears to float with subtle soft drop shadow giving digital layer tangible sense of levitation
- **Lighting Quality:** Masterclass in virtual studio setup diffuse shadowless perfectly even, Dark Mode background absorbs light like matte black marble providing infinite depth while UI elements catch gentle cool-toned ambient light, active tabs feature subtle warm gradient sheen mimicking reflection of softbox on polished glass
- **Color Grading:** Sophisticated restrained adhering to luxury monochromatic scheme, deep charcoals and true blacks dominating negative space creating premium OLED black aesthetic, text rendered in crisp sterile whites with perfect kerning, links utilize muted desaturated blue-purple avoiding garish primaries, color grading intentionally cool clinical evoking precision engineering
- **Motion Sequencing:** Frozen moment of anticipation hero pause in user journey, hand-shaped cursor positioned delicately over link suggesting split second before interaction implying smooth liquid motion sequence where scroll has just completed

### v2_f540.jpg
- **Hero Render Treatment:** Interface treated with spatial depth utilizing heavy frosted-glass translucency glassmorphism on main window, Exploded View selection acts as hero moment singular sharp focal point emerging from sea of soft organized data, window floats above desktop landscape with subtle drop shadow creating distinct z-axis separation mimicking physical layering
- **Lighting Quality:** Cinematic ambient occlusion defines scene, warm low-angle light source emanates from desktop wallpaper horizon glowing amber and gold city lights seeming to back-light lower edge of UI, interface itself lit by diffuse cool overhead equivalent ensuring white text pops against deep charcoal backgrounds without harsh specular highlights
- **Color Grading:** Rich twilight palette dominates, deep saturated violets and magentas in upper sky gradient transitioning seamlessly into warm earthy ochres and burnt oranges near bottom, UI anchors this with neutral near-black gunmetal greys allowing vibrant background to breathe while maintaining premium dark-mode aesthetic
- **Product-as-Artifact Composition:** Selected file framed with reverence of museum artifact isolated by bright blue selection box and soft blur of rows behind, title suggests deconstruction and engineering perfection treating digital file not as data but as tangible object of precision craftsmanship

---

## V4 Frames — Web Design Course (GSAP/Development Focus)

### v4_f15.jpg
- **Layout:** Centered hero MacBook Pro dominating viewport, immersive negative space black void surrounding product eliminating distractions forcing viewer eye directly to brightly lit screen, screen-within-screen showing macOS application running demonstrating product in use rather than static object, compact fixed top navigation keeping utility accessible
- **Typography:** San Francisco font family, MacBook Pro bold white establishing subject clearly, muted grey navigation links indicating secondary actions, blue pill CTA button with white text acting as primary call-to-action
- **Color Palette:** Monochromatic OLED black (#000000) signaling luxury premium tech allowing screen content to pop, vibrant neon cyan electric blue bright yellow on laptop screen creating high-saturation contrast against void background

### v4_f300.jpg
- **Layout:** Centered wizard/onboarding layout vertically horizontally centered minimizing distractions guiding user strictly toward task, card-based hierarchy with main interaction area within subtle light-grey container separating active task from page rest, fixed footer anchoring navigation controls and progress bar always accessible regardless of scroll position
- **Typography:** Clean sans-serif modern geometric (Manrope/Inter style) conveying tech-savviness readability, strong weight contrast between primary question bold dark charcoal and explanatory subtext regular lighter grey, input label small uppercase spaced out sitting just above input field for clarity
- **Color Palette:** Dominant pure white providing clean slate feeling essential for setup flows, brand lavender/lilac primary accent used for top banner input focus state and progress bar creating friendly approachable vibe, status coding soft green for Owned badges success safety muted pink/red for Expired badge signaling caution

### v4_f900.jpg
- **Layout:** Classic three-pane layout optimized for productivity, left sidebar approximately 20% width housing project file tree, center pane main workspace currently empty with cursor line visible, right pane stark black panel displaying Hello world output suggesting live preview or terminal, slim header containing project name and toolbar with action icons
- **Typography:** Strictly monospaced Consolas Menlo or Caskaydia Cove essential for aligning code characters vertically, small compact text approximately 11–13px maximizing information density, file names crisp white/light gray breadcrumb path slightly dimmer muted gray receding visually
- **Color Palette:** Deep Dark theme, deep charcoal/navy blues (#1e1e1e to #252526) reducing eye strain providing high-contrast canvas, selection vivid electric blue (#264f78) highlighting selected folder, syntax/icon colors cyan for JavaScript TypeScript files yellow for configs blue for HTML/CSS

### v4_f1800.jpg
- **Layout:** Split-pane workflow layout commonly found in developer environments, left panel code editor occupying approximately 60% screen featuring vertical file navigation breadcrumb at very top and vertical ruler margin on far left for line numbers, right panel browser preview occupying remaining 40% displaying live rendering of webpage
- **Typography:** Editor uses monospaced font JetBrains Mono or similar optimized for readability employing distinct syntax highlighting keywords in soft lavender pink JSX tags in neon green strings in warm orange yellow, web page uses clean sans-serif Apple San Francisco bold white headers stylized gradient headline small muted grey pricing details
- **Color Palette:** Dark mode both panels deep charcoal black (#1e1e1e editor background true black #000000 web page background), active selection semi-transparent dark teal green bar highlighting currently selected block, vibrant multi-color gradient cyan magenta yellow on hero text simulating RGB lighting effect vivid royal blue CTA pill standing out sharply

### v4_f2700.jpg
- **Layout:** Split-screen layout common in developer documentation tutorials or live coding environments, left panel approximately 65% width dedicated to code editor interface displaying vertical stack of JSX React code, right panel approximately 35% width serving as presentation preview window featuring dark mode canvas with centered 3D object peripheral UI controls
- **Typography:** Code editor uses monospaced font Fira Code JetBrains Mono or similar essential for programming readability small but legible prioritizing density of information, preview area uses clean lightweight sans-serif Apple San Francisco style headline Take a closer look large bold white creating strong focal point secondary text bottom smaller subdued providing context without distraction
- **Color Palette:** Backgrounds deep monochromatic darks code editor dark charcoal slate standard IDE backgrounds right panel pure black #000000 simulating void making 3D model pop, syntax highlighting vibrant high-contrast One Dark Dracula themes cyan light blue for keywords purple pink for imports teal green for HTML-like tags

### v4_f3600.jpg
- **Layout:** Split-screen layout approximately 55/45 ratio, left panel dense vertical code editor environment resembling VS Code featuring file tabs at very top and sidebar minimap on far right edge, right panel spacious immersive product showcase area using hero-layout style significant negative space black void focusing attention on central 3D object, thin horizontal guidelines orange/red extending from right-side UI elements back toward code on left visually linking output to source code
- **Typography:** Code side uses monospaced font Fira Code JetBrains Mono standard for developer tools functional varying weights denoting logic bold versus data, preview side uses clean lightweight sans-serif San Francisco style headline Take a closer look small tracked out letter-spaced conveying sophistication bottom labels also small understated
- **Color Palette:** Unified Deep Dark theme near-black backgrounds like #0d1117 standard Darcula Dracula themes reducing glare creating premium high-contrast canvas, syntax highlighting pastel low-saturation palette neon green teal for keywords imports soft yellow amber for component tags string literals muted blue for function names variables

### v4_f4800.jpg
- **Layout:** Vertical split-screen layout hallmark of modern developer environments VS Code paired with hot-reload browser tab, left pane editor dominated by code density but organized with clear left-margin for line numbers indentation, right pane preview shows macOS window frame containing rendered result WYSIWYG arrangement creating direct cognitive link between logic code and output visuals
- **Typography:** Monospace editor font sleek variant like JetBrains Mono Fira Code characters distinct widely spaced enough for comfort during long coding sessions, system UI font preview on right uses clean standard sans-serif Helvetica Inter typical for high-end tech product launches, code shows clear typographic hierarchy through color coding keywords purple strings orange HTML tags blue
- **Color Palette:** Strictly dark mode aesthetic associated with premium developer tools base colors deep charcoal near-black backgrounds (#1e1e1e range) reducing eye strain content pop, syntax highlighting soft pastel-inspired palette instead harsh neon colors chosen muted corals soft blues dusty purples giving interface sophisticated calm focus vibe, soft mint-green vertical bar acts as subtle scrollbar visual anchor

### v4_f6000.jpg
- **Layout:** Layered multi-pane layout typical of modern developer environments IDEs, split focus background layer likely code editor foreground overlays, left centralized command menu floats in void right distinct vertical floating panel AI assistant overlays workspace mimicking native macOS window title bar traffic light controls back arrow creating sense depth modality over underlying code
- **Typography:** Clean geometric sans-serif typeface used for UI labels body text ensuring high readability monospace accents keyboard shortcuts code snippets utilize monospace font dual-font strategy immediately signals technical tool, primary headings bold white secondary instructions softer gray metadata file names line numbers smaller muted
- **Color Palette:** Deep dark mode background very deep cool-toned charcoal midnight blue close to VS Code default dark theme colors #1e1e1e #0d1117 reducing eye strain standard premium dev tools, accent colors mint green used for file paths positive actions checkmarks syntax highlighting provides vibrant pop against dark background without being neon, cyan blue used for interactive elements Stop pill button selected text muted grays used for borders inactive text placeholders creating calm non-distracting environment

### v4_f7200.jpg
- **Layout:** Split-pane layout typical of modern Integrated Development Environments IDEs like VS Code, primary editor left occupies roughly 75% horizontal space dedicated entirely to code editor, preview pane right narrower column roughly 25% displays live visualization simulation of code specifically showing 3D MacBook mockup floating in dark void, compact header row containing file breadcrumbs and macOS window controls traffic light dots
- **Typography:** Monospace font clean high-readability JetBrains Mono Fira Code or similar font size comfortable for coding approximately 12–14px equivalent subtle weight variations distinguishing semantic types bold keywords versus lighter strings, indentation strict consistent nested brackets arrows visually mapping component hierarchy
- **Color Palette:** Deep Dark Mode palette characterized near-black background (#1e1e1e or #0d1117) reducing eye strain, syntax highlighting vibrant distinct against dark background magenta purple used for hooks useRef constants import statements cyan blue used for component names Suspense lens lime green used for string literals text inside quotes orange yellow used for numeric values boolean props grey white used for standard operators plain text nodes
- **UI Elements:** Minimap scrollbar visible on far right edge thin vertical teal line scrollbar minimap indicator soft green accent

### v4_f8400.jpg
- **Layout:** Center-aligned vertical stack strict central axis Apple logo navigation headline product imagery Call-to-Action all perfectly centered horizontally creating sense balance stability focused attention, heavy negative space incredibly sparse vast amount screen pure black void hallmark luxury tech design forcing eye to only two focal points text and device, clear top-down flow Navigation → Product Name → Value Proposition Gradient Text → Product Visual → Primary Action Buy → Secondary Info Pricing
- **Typography:** San Francisco font family characterized neutrality high legibility variable weights MacBook Pro standard medium Built for Apple Intelligence significantly larger bolder subdued utility text pricing information navigation links rendered smaller lighter grey opacity receding background until needed maintaining premium uncluttered feel
- **Color Palette:** True black #000000 specific to Apple Pro product lines iPhone Pro MacBook Pro conveying sophistication hardware focus, vibrant gradients glowing horizontal cyan to magenta to orange on headline breaking monotony black white scheme visually representing energy neural networks associated with AI, rim lighting MacBook development environment creating tangible depth presence

---

## Cross-Video Synthesis — Key Design Patterns

### Color Grading Principles
1. **Void Black Dominance:** Deep near-blacks (#050505–#0D1117) as primary background — never flat black but rich charcoal gradients
2. **Desaturated Sophistication:** Muted editorial palettes with narrow tonal bands — saturation reserved for single accent purposes
3. **Strategic Accent Pop:** One dominant accent hue per composition (amber/gold, neon mint, coral orange) used exclusively for CTAs/highlights
4. **Semantic Color Coding:** Green for positive/success, amber for warnings, red/crimson for critical alerts — never decorative
5. **Warm vs Cool Balance:** Warm blacks with amber undertones (#0D1117) feel more premium than clinical blue-grays (#0B0F17)
6. **OLED Black Specificity:** Pure #000000 used specifically for Apple Pro product lines conveying sophistication

### Typography Anatomy
1. **Dual-Font System:** Geometric sans-serif (Inter/SF Pro) for UI chrome + Monospace (JetBrains Mono/Fira Code) for data/numerics
2. **Tabular Numerals:** Every numeric value uses tabular-nums for alignment stability in tables/charts
3. **Weight Hierarchy Over Size:** Heavy bolding distinguishes headers from body rather than relying solely on point size
4. **Tracking Discipline:** Tight tracking (-0.02em to 0em) on display headlines, relaxed spacing (0.05em+) on body text
5. **Case Variation:** Uppercase for section labels and metadata, mixed case for primary content
6. **Brutalist-Editorial Mix:** Massive heavy-weight sans-serif paired with italicized serif quotes for literary weight

### Depth & Lighting Techniques
1. **Rim Lighting Separation:** Single-directional rim light traces object contours separating form from dark background
2. **Subsurface Scattering:** Translucent materials (silicone, leather, glass) show internal light diffusion adding tactile warmth
3. **Controlled Specularity:** Elongated soft-edge highlights slide fluidly over curved surfaces indicating material type
4. **Glassmorphism Reserve:** Frosted glass (backdrop-filter blur 12px) used only for nav bars and modals — never on data tables
5. **Gradient Falloff:** Backgrounds use radial/vertical gradients center-lifted to edges-deeper creating vignette depth without UI chrome
6. **Atmospheric Scattering:** Volumetric fog/atmosphere creating depth layers behind subjects
7. **Low-Key Chiaroscuro:** Dramatic single-source lighting with deep shadows pooling into recessed areas

### Motion Choreography
1. **Duration Scale:** Micro-interactions 150–200ms, component reveals 300–400ms, scroll animations 600–700ms, hero numbers 900–1200ms
2. **Easing Family:** Primary ease-out cubic-bezier(0.16, 1, 0.3, 1) for snappy start/soft landing; spring easing for button press feedback
3. **Staggered Grouping:** Content reveals in 80ms intervals across sibling groups creating orchestrated page-load sequence
4. **Count-Up Animation:** Numeric values animate from 0→target over 900ms with fast-start/slow-decel easing
5. **Parallax Subtlety:** Background parallax limited to 2–4px shift — noticeable but not distracting
6. **Orbital Smoothness:** Slow buttery-smooth orbital dolly around products with parallax creating profound 3D sense
7. **Exploded View Transitions:** Slow smooth disassembly into component parts hovering revealing internal complexity

### HUD/Data Display Anatomy
1. **Monospace Numerals:** JetBrains Mono or similar with tabular-nums on every changing number
2. **Hairline Separators:** 1px lines at rgba(241,245,249,.08) for table borders and dividers
3. **Status Dots:** 3px colored circles paired with monospace labels for state indication
4. **Sparkline Compression:** 24px height, 1px stroke, no grid lines — pure signal data
5. **Value Emphasis:** Key metric rendered 2–3x larger than label with slightly higher luminance/brightness
6. **Peripheral Metadata:** Navigation and data pushed to absolute edges keeping center stage clear

### Layout Composition Rules
1. **Screen-within-Screen:** Hardware frames (MacBook, phone mockups) elevate digital interfaces into tangible objects
2. **Centered Hero Void:** Full-bleed black background with centered product creates museum-display reverence
3. **Split-Pane Workflow:** Developer-style splits (code/preview) create cognitive link between logic and output
4. **Peripheral Navigation:** Critical controls pushed to edges/corners keeping center stage clear for content
5. **Asymmetric Balance:** Heavy typographic blocks balanced against visual subjects following rule-of-thirds
6. **Modular Dashboard Grid:** Persistent vertical rails flanking central multi-column content areas
7. **Zenith-Focused Stack:** Centered vertical hierarchy with floating action button anchoring viewer attention

### What to AVOID (Costume vs Craft)
- ❌ Cyan glow on everything
- ❌ Scan-line overlays
- ❌ Pulsing borders
- ❌ Corner brackets as decoration (use only for functional HUD framing)
- ❌ Projected-text drop shadows
- ❌ Excessive neon saturation
- ❌ Marvel/superhero theming (Iron Man aesthetic is craft reference ONLY)
- ❌ Red glow effects (Iron Man chest piece association)
- ❌ Metallic/industrial textures (superhero suit association)
- ❌ Dramatic character lighting (rim light OK, spotlight NO)
- ❌ Comic-book typography (bold slanted fonts)
- ❌ Particle effects and explosions
- ❌ Shield/logomarks that resemble armor

**Remember:** The discipline is premium, not the costume. ScoutVeda is a professional SaaS for Amazon sellers — not a movie prop.

---

## Frame Inventory

| Video | Frames Analyzed | Purpose |
|-------|----------------|---------|
| v3 (Iron Man UI) | f2, f8, f15, f22, f30, f40, f50, f60, f70, f80, f88 | HUD layout, color grading, motion cues, developer workflows |
| v1 (3D Websites) | f2, f5, f8, f11, f14, f17, f20 | Hero renders, lighting, typography, 3D composition |
| v2 (Apple Product) | f5, f90, f180, f270, f360, f450, f540 | Hero treatment, material rendering, motion, exploded views |
| v4 (GSAP Course) | f15, f300, f900, f1800, f2700, f3600, f4800, f6000, f7200, f8400 | Code editors, dev workflows, layout patterns, Apple aesthetics |

---

*Raw JSON data available in FRAME-ANALYSIS-Raw.json*
*Previous version dated 2026-09-21 — updated with full frame-by-frame analysis*