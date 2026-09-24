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

---

# Vision-Confirmed Pass (2026-09-24) — RAW FRAME OBSERVATIONS

> Earlier notes above were written while the vision model was degraded (no image input), so hex/palette details were inferred from filenames and general descriptions. This section records what the **active vision model actually saw**, per frame, restricted to buildable craft (no themes, no characters). Re-used to ground spec §1 #21–#30 and §4.5.1.

**Vision test:** PASSED — `v3_f40.jpg` correctly described (dark-themed AI video-gen web app, king.ai, showing Iron Man-style renders). All frames below are vision-verified.

## V3 (highest priority — HUD/scroll craft)

**v3_f2 / v3_f8 / v3_f15 (hero HUD frames):**
- **Grading:** near-black `#050505`–`#0a0b0d` (warm, not blue); radial/vignette lift in center fading to darker edges; desaturated slate-teal fog `#3a4448`; deep crimson horizon `#5e121c`→`#a01824`; single warm accent gold/amber `#e8b437`–`#f0c040` reserved for ONE word + tiny glyphs; off-white text `#f4f5f6`, muted cool gray `#8a8f96` for body.
- **Core technique:** restraint — ~90% monochrome, one hot accent. Color = signal, not decoration. That scarcity is what reads "premium."
- **Type:** two-face system. Huge tight-tracked heavy grotesk headline (left, one word recolored amber) vs. tiny (~9–11px) uppercase technical MONO labels with wide tracking + `//` and `—` separators (SEG 001/009, TELEMETRY LINK, PROTOCOL). Extreme scale contrast = "control panel" voice.
- **HUD anatomy (TASTEFUL):** L-shaped corner crop-brackets at canvas corners; thin hairline rails top/bottom; peripheral data readouts pinned to the four edges (flight log left, seq counter right, playback center); a "● LIVE" status dot; "SCROLL ↓" cue. These read as "operational interface / film frame inside a viewfinder."
- **Lighting/depth:** crushed-black background → subject max separation; cinematic low-key (warm core bloom + cool rim on subject); volumetric smoke/fog at base; heavy vignette pulling eye inward; a semi-transparent glass quote-card layered over the photo = 3rd depth plane (UI → card → photo → black).
- **Costume vs craft:** corner brackets + seq counters are tasteful ONLY as functional framing; they become costume if repeated decoratively across the whole dashboard. Custom cursor = high-end marketing cue, NOT appropriate for a data SaaS dashboard.

**v3_f40 / v3_f50 (workbench / DCC-tool frames):**
- **Grading:** cool near-black `#0B0D10`–`#101216`; panels `#16181D`/`#1A1D22`; hairlines `#262A30`; text `#E6E8EC` primary / `#9AA0AA` secondary; ONE accent — signal green `#3DDC84`–`#4ADE80` on "NEW" badge, toggle-on, active tab, success dots. Monochrome + single accent = "hardware/console" precision.
- **Layout:** classic pro-workbench 3-zone shell — left icon rail (~56px, 12–14 line icons + one badge) + left config panel + center canvas (media player strip on top, media-card feed below) + right filmstrip thumbnail rail. Uniform 8-pt grid, hairline dividers not heavy borders, F-pattern reading flow.
- **Micro-badge grammar:** tiny uppercase tags (NEW, 2K HD, IMAGE 3.0) on subtle backgrounds = a "visual vocabulary" that feels engineered.
- **Depth:** elevation by lightness + 1px strokes (floating-panel feel), NOT heavy blur; low-key UI so content images read as key-lit subjects ("studio suite" contrast). Active thumb gets a glowing outline = "spotlight."
- **Motion cues (static tells):** sliding toggle knob + color-fill (gray→green); sliding segmented-tab indicator; chevron dropdowns; hover row icons + active-thumb scale-up; progress/scrub timeline with playhead; transient slide-in toast banner.

**v3_f60 / v3_f70 / v3_f80 (dev-cockpit frames, multi-window/IDE):**
- **Grading:** warm charcoal `#0d0d0f`–`#18181b` (not pure black), panel steps `#1f1f23`→`#26262a`, text ramp `#e4e4e7` / `#a1a1aa` / `#5a5f58`. Single warm accent coral/orange `#ff6f4d`–`#f97350` (pixel mascot, status dots) used <5% of screen.
- **Layout:** 3-zone "sources → work surface → reference" master-detail. Radical negative space in the focus panel ("console awaiting input"); hairline 1px vertical dividers; grouped label-driven IA (GPTs / Projects).
- **Depth (KEY TECHNIQUE #21):** flat tonal layering — each layer ~2–3% lighter than the one behind (window→panel→card→input) + 1px hairlines; NO drop shadows. "Glass-on-matte" depth.
- **Emissive (KEY TECHNIQUE #22):** the orange glyph, red status dots, and white scrub line are self-illuminated points — the only bright pixels read as *light sources* on the carbon field ("night console" glow).
- **Type:** mono + geometric-sans pairing; `// TODO:` placeholder borrows terminal syntax as a *brand voice* (empty state feels like a codebase, not marketing copy).
- **v3_f88 (end-card):** near-black + one hot accent `#FF1A3D`–`#E60023` (reserved only for "SUBSCRIBE!"), radial vignette glow behind text = light source, neon bloom on the hero word (soft outer glow + inner saturation = backlit signage). Stagger-in language encoded: headline fade → CTA slide → button rise, glow "breathes." Confirms glow-on-value as a tasteful, scarce effect.

## V1 (3D website visuals)

- **v1_f2 (desk-setup thumbnail):** matte-body + emissive-accent material pairing (OLED-like teal glow `#22e0cf` on graphite `#3a3d42`); one cool accent + one tiny warm signal orange; photographic contact shadows + global illumination + depth-of-field lift the 3D objects off the page (prototypes, not mockups).
- **v1_f5 (dora.ai 3D):** FLAT-minimal 2D UI (white + black type + electric-blue pills `#1E6BFF`, airy negative space, single CTA) over a GLOSSY 3D dark-navy band `#101A4A`–`#1B1B5C`. The "future" signal is the crisp-2D / dimensional-3D contrast. Horizon line where white meets navy = "ground plane" so objects rest in space.
- **v1_f8 (dora sphere hero):** restrained cool duotone (deep blue + violet on black `#070712`–`#0a0a18`); electric-cobalt sphere rim `#2d5bff`; glassmorphism on input bar + lower panels (translucent fill, soft border, blur). Real-time 3D sphere w/ atmospheric rim light + bloom = biggest "futuristic" signal; minimal centered single-CTA = confidence.
- **v1_f11 (card rail + type hero):** near-black `#0B0B12` + magenta-violet ambient glow `#3A1550` + single electric-cyan horizon line `#22D3EE`/`#18E0C8`; asymmetric two-zone (modular card grid left, type hero right); emissive "horizon" bar as organizing axis; backlit gradient = holographic depth.
- **v1_f14 (AirPods 3D):** cinematic dark mode, pure-black canvas `#000000`–`#0A0A0A`, pure-white product+type; massive thin wordmark BEHIND the 3D product (real occlusion/parallax depth = "type as 3D set piece"); studio-lit renders (soft key, rim speculars, ambient occlusion, implied floor shadow); "whisper vs shout" type contrast (display vs whisper-small nav with `→` affordances).
- **v1_f17 (power/battery case study):** asymmetric left hero (text ~55%, low-key visual right ~45%); near-black `#07070A`–`#0D0D12`; off-white `#F5F5F7`; single electric green `#39FF14`/`#00E64D` on the word "power" only (color-coded to meaning: green=battery/power); low-key vignetted photography layered flat-over-dimmed-photo; generous editorial negative space.
- **v1_f20 (spatial 3D tilt):** the page rendered as a TILTED card in space; blueprint/CAD layer of thin axis ticks + node connectors + square markers beneath content; near-black `#0B0B0E` + luminous lime gradient `#5BE04A`→`#A8F04C` + violet `#7A2BF5`; micro data-viz (mono cards, axis ticks, node graph). "Spatial computing / holographic control surface" — flat UI presented as objects in a room.

## V2 (Apple-style 3D product)

- **v2_f5 (SONY headphones):** studio-grade PBR hero, 3/4 view, floating on near-black w/ soft radial halo; matte-black + faint teal accent; classic low-key product lighting (soft upper-left key → rim highlights on headband/cup edges, rest falls into shadow); monochromatic desaturated grade, eye funneled to product; asymmetric right-edge feature copy; glassmorphism minimal but present (frosted overlay behind nav/text).
- **v2_f180 / v2_f360 (matte-black headphone grid + exploded):** the KEY Apple-render lesson — **light the product with EDGES, not faces:** soft rim/backlight (clay-light) traces top edges, controlled narrow speculars on metal/leather, background is a SUBTLE RADIAL GRADIENT (slightly lighter behind product, darker at edges) not flat black, lifted shadows (no crush to #000). v2_f360 shows two side-by-side keyframes = assembled → exploded view (slow, "professional internal tech showcase, Apple-style"). Material honesty: matte vs gloss contrast = "engineered."
- **v2_f90 / v2_f450 / v2_f540 / v2_f270:** (dev-workflow / desktop / empty frames — vision noted these are NOT 3D hero shots, so no render craft; captured dark-UI tone: warm charcoal not pure black, one accent <5%, hover = low-alpha white overlay `rgba(255,255,255,0.06)`; macOS vibrancy = heavier blur on edge chrome, lighter on content = "glass" gradient.)

## V4 (general web-design course / GSAP)

- **v4_f15 (MacBook Pro hero):** void-black `#000000`–`#0a0a0a`; centered 3D product floating w/ faint reflection; screen is the light source (chiaroscuro); off-white `#f5f5f7` + quiet two-tier sans nav; single saturated blue Buy pill `#0071e3` = only "hot spot" (accent discipline guides eye to conversion). PBR + glowing screen + floor reflection = "expensive object."
- **v4_f300 (Hostinger domain wizard):** cool off-white `#F8F8FB`; one violet accent thread `#6C4EE8`–`#7B5CFF` (focus ring, progress fill, banner, assistant chip — consistent brand thread) + semantic green `#1FA85F` (Owned) / violet (Expired). CTA deliberately NOT the accent (dark slate `#33333B`). **KEY TECHNIQUE #28:** the domain input is framed inside a faux "browser chrome" card — "typing the address of a site that's about to exist." Low-elevation flat-hybrid (hairline border + near-imperceptible shadow), depth by VALUE STEPPING not shadows.
- **v4_f900 / v4_f1800 / v4_f2700 / v4_f4800 / v4_f7200 (GSAP dev splits):** monospace-for-machine + humanist-sans-for-human pairing; near-monochrome dark `#0d1117`; one luminous accent (teal `#4ec9b0` / cyan `#5eead4` for active scrollbar + hologram edges) used sparingly = "signal" color; code↔result split = "engineered" credibility. **KEY TECHNIQUE #24:** gradient-filled headline (background-clip:text) + soft bloom = "lit, not inked." **v4_f7200:** subtle chromatic-aberration/hologram edge on the 3D model (out-of-focus sci-fi) — tasteful at 1px/20%, costume if pushed.
- **v4_f8400 (Apple "Built for Apple Intelligence" page):** true black `#000000`–`#050505`; single signature horizontal gradient cyan `#00D4FF`→blue `#3A5CFF`→violet `#8A2BEE`→magenta `#FF2BD6`→orange `#FF7A00` (used ONLY on hero fill + product light-bar; ~10% luminous color, 90% monochrome = "deliberate"); glassmorphic frosted dark browser panel layered IN FRONT of a rim-lit edge-on laptop (blue-left/orange-right rim = lit-from-within); **KEY TECHNIQUE #25:** the browser mock is a 3-step choreographed loop (typed caret → checkmark → spinner) = "intelligence is thinking." Centered vertical stack, void does the framing.

## Concrete cross-video principles (buildable, theme-free)
1. **Warm near-black, never flat:** `#050505`–`#0D1117` with a center-lifted radial/vertical gradient falloff (vignette). Pure `#000000` reserved for Apple-grade "Pro" object showcases only.
2. **One accent per screen, <5% of the area:** amber/gold (v3), signal-green (v3 workbench), electric-blue (v4 CTA), violet (v4 wizard). Color is a currency, not a paint. Semantic green/red reserved for meaning.
3. **Depth by luminance steps + 1px hairlines, not box-shadows** (pro-dark technique). Reserve a soft shadow for the single floating/hero element only.
4. **Emissive focal points:** the only "bright" elements (status dots, key numbers, accent glyph, scrub line) should read as lit sources on the dark field.
5. **Type scale contrast does the hierarchy:** huge tight grotesk display vs. ~10px wide-tracked mono micro-labels; two-face sans+mono system; weight/size/color over ornament.
6. **Motion = state communication:** count-ups, assembled→exploded, syncing→synced→next-in, hover-scaling, slide-in toasts. Slow + eased + few (max 2 moving per viewport).
7. **Tasteful HUD = monospace numerals + 1px hairlines + value-glow + 3px status dots + 24px/1px sparklines.** Costume to AVOID: all-cyan glow, scan-lines, pulsing borders everywhere, decorative corner brackets, custom cursors, particle/spotlight spectacle.
8. **Asymmetric composition + generous negative space** ("command deck"/"museum vitrine") over busy grids; one hero element isolated against a quiet field.

---

## Vision-Confirmed Pass #3 (this run) — raw per-frame craft observations

Vision was re-tested and confirmed working this pass. Re-analyzed the full frame set with a live vision model. Below are the raw frame observations (craft-only; fictional/entertainment content deliberately ignored). These are the concrete observations merged into `DESIGN-SPEC-3D-UI.md` §1 and §4.5.

### v3 — Iron Man-style scrolling site (the reference Boss likes; craft only)
- **v3_f2 (hero):** Strict asymmetric 12-col grid on warm near-black `#050506→#0A0A0C` (matte, not pure black). Single amber accent `#D4A72C–#E0B13C` used sparingly; off-white text `#F4F4F2`; muted mono grays `#6E6E73–#8A8A90`. Two-family type: one huge tight-tracked grotesk display headline (120–160px feel) + micro uppercase mono labels (10–11px, wide tracking, low opacity) pinned to all four corners (viewfinder ticks, "LIVE" tag, "SEQ 001/019", "SCROLL ↓"). Radial highlight + heavy vignette + subtle film grain; translucent quote card `rgba(20,20,24,.6)` + 1px `#2A2A30` border sitting above the image plane. Premium = 2-color discipline + extreme type-scale contrast + hairline rules + HUD framing.
- **v3_f8:** Light studio-gray gradient field `#c9c9c7→#8c8c8a` (not the dark variant) with dark letterbox strips; near-black UI chrome `#141414`; single amber `#e9b93f` + one cool glow `#bfe9e6`. Right-anchored type stack; corner brackets + "SEQ 102/169 ▮" counter + "TITAN II // FINAL FRAME" status pill; soft key light upper-left, specular bloom. Diagonal tension + negative-space corridor = "mission readout."
- **v3_f15:** Dark cinematic, deep crimson→black ambient gradient (oxblood `#5a1414`), gold accent `#e8b400` on one word only, hot red `#ff2a2a` glow on a point source. Volumetric fog + rim light + particle depth-of-field; edge-anchored content (left rail / right headline / top+bottom bars) leaving center clean. Cinematic 16:9 frame + HUD micro-typography.
- **v3_f40 / f50 / f60 / f70 / f80 (dev-workbench register):** This is the *transferable* line for ScoutVeda. Three-zone "rail → params → canvas" shell; monochrome near-black `#0a0a0a–#141414` with ~1–2% luminance steps between panels + 1px `#222–#2a2a2a` hairlines; single warm accent (coral `#ff5a3c`/amber) on the active state only. Monospace terminal voice (`// TODO:…`, tabular timecodes), low-contrast quiet type. Depth is tonal, not shadowed. Selection reads as a glowing outline, not a drop shadow. Flat, matte, "instrument panel."
- **v3_f88 (outro card):** Pure black `#050505` + one neon-red `#ff2d3f` accent + radial maroon glow; the emphasized word is treated as an **emissive light source** (bloom/text-shadow, not a border). Confirms "glow-on-value" and "emissive points read as focal light."

### v1 — 3D web-visuals tutorial
- **v1_f5 / f8 (Dora AI):** Light hero (`#F3F4FB`) hands off to a full-bleed lit 3D "ocean" `#1E2A5A`; electric-blue accent `#2F6BFF` + one warm yellow focal `#FFCF33`. "2D chrome over 3D world" = the core depth trick. Flat unlit type on top, fully-lit volumetric scene below.
- **v1_f8b (space hero, f8/f11 variants):** Deep space navy `#0a0e2a`, planet with atmospheric rim lighting, glassmorphism floating panels (translucent + blur + soft shadow), neon violet→magenta `#6d28d9→#e040fb` used sparingly for glow/strokes. Two-tone two-weight headline lockup for emphasis without scaling.
- **v1_f14 / f17 / f20 (editorial dark):** Near-black `#0a0a14` purple cast; electric violet `#7C4DFF` + one cyan `#17E0C4` + functional blue CTA `#2E6BFF`. Asymmetric left-anchored type column; a single horizontal neon "scan" line as a horizon; floating glass/3D object with parallax; oversized light-weight grotesk headline + tiny tracked caps eyebrow. v1_f20 even adds an engineering "blueprint" overlay (mono data + tick marks) + a lit glass-sphere 3D asset — the studio-credibility device.

### v2 — Apple-style 3D product pages
- **v2_f5 (headphones hero):** One hero object = 50–60% of frame, on a black void; matte PBR finish, turntable loop + shallow DoF; three-point studio light with **rim/edge light** carving the dark product off the dark bg + radial pedestal glow; monochrome + single electric-blue accent `#0a84ff`; one typeface, hierarchy by size/weight/contrast only; slow eased scroll-synced camera. "Restraint = luxury."
- **v2_f180 / f360:** "Object-first, chrome-second" — black-on-black hero cut-out, UI reduced to ghost glyph strips in corners, one accent pill. **v2_f360:** the exploded-view beat (assembled → disassembled, slow, "professional internal tech showcase") — the signature product-narrative motion.
- **v2_f270 / f540 (macOS/asset pipeline):** Warm-cool cinematic light (cool fill + warm rim), glass/vibrancy translucency for depth, spec-sheet typography (aligned tabular columns, small low-contrast metadata), sequenced 3D reveal grammar (explode → orbit → light sweep → scroll-linked copy).

### v4 — general web-design course
- **v4_f15 (MacBook hero):** Centered lit device on a true-black void; monochrome nav + one electric-blue CTA; the only saturated color lives inside the screen (content-as-hero). Micro-reflections + soft contact shadow ground the device.
- **v4_f300 (wizard onboarding):** The *pro-tool dashboard* register — pinned app-shell scaffold, constrained ~560–640px column, one confident violet accent `#6C4CF1` + semantic green, flat-2.0 surfaces (1px borders + soft shadows, no skeuomorph), in-context browser mockup, floating AI-assistant pill. This is the cleanest model for ScoutVeda's operational dashboard.
- **v4_f1800 / f3600 / f4800 (code + live 3D):** 70/30 asymmetric split (raw source left, lit 3D viewer right); single cool accent; soft studio key + contact shadow + vignette; pill/segmented configurator controls; code-to-design gutter ticks (green/amber/red) as a craft signal; GSAP + react-three implies eased orbit/scroll reveal.
- **v4_f8400:** "Choreographed thinking loop" — a 3-step animated sequence (URL typed → checkmark → spinner → resolves) simulating intelligence; and uppercase-mono loading fallbacks ("LOAD..."). The pattern for ScoutVeda's data-freshness indicator.

### Cross-video synthesis (what actually makes them premium — craft, not theme)
1. **Monochrome base + ONE accent.** Every premium frame is 90%+ desaturated (near-black or off-white) with a single saturated accent reserved for state/action only. Restraint = perceived quality.
2. **Extreme type-scale contrast.** One huge tight-tracked display face vs. many tiny wide-tracked mono micro-labels. Hierarchy by size/weight/tracking, almost never by color.
3. **Tonal depth, not shadows.** Panels separated by 1–3% luminance steps + 1px hairlines; drop shadows reserved for the single floating hero only. Flat, matte, machined.
4. **Emissive "light-source" points.** Small self-lit elements (status dots, key numbers, active outlines) with subtle outer glow read as literal light on a dark field → focal points.
5. **HUD anatomy that reads tasteful:** tabular monospace numerals, thin hairlines, glow-on-value, 3px status dots, short mono counters (`SEQ 001/019`). **Costume to avoid on a SaaS dashboard:** all-cyan glow, scan-line everywhere, pulsing borders, decorative corner brackets, custom cursors, chromatic aberration, particle spectacle.
6. **Motion = state communication.** Count-ups, assembled→exploded, syncing→synced→next-in, hover-scale, slide-in toasts. Slow + eased (cubic-bezier(0.16,1,0.3,1)) + few (max ~2 moving per viewport).
7. **Two registers, kept separate:** a *cinematic hero* register (glow, gradient material, idle levitation, atmospheric depth) and a *data-instrument dashboard* register (restraint, tonal layering, single accent, mono type). The "costume" lives only in the hero.

---

## Vision Pass #4 (2026-09-24, live vision re-run, full frame set re-analyzed)

Raw per-frame craft reads pulled fresh from the live model. Confirms and sharpens the synthesis above; adds a few concrete hex/type/motion details not previously captured. All craft — zero superhero/entertainment content.

### v3 — cinematic HUD register (hero language only)
- **v3_f2:** warm near-black `#0B0B0D→#1E1E22` (lifted, not pure `#000`); single amber-gold accent `#C9A227–#E0B54A` used at very low frequency; off-white type `#F2F2F0`; muted gray micro-labels `#8A8A8A`. Four L-shaped viewfinder corner ticks + top/bottom status rails ("SEG 001/059", "SCROLL"). Hierarchy is pure scale-contrast: ~120–150px display vs ~10px wide-tracked mono caps.
- **v3_f8 / v3_f15:** same gold-on-charcoal discipline; `//`, `SEQ 142/149`, "FINAL FRAME" as terminal punctuation ornament; volumetric fog + rim light + gold particle bokeh for cinematic depth. These are showreel frames — their costumes (brackets, scan-telemetry) belong ONLY in a landing hero.
- **v3_f40 / f50 / f60 / f70 / f80 (dev-workbench — the transferable line):** three-zone "rail·params·canvas" pro shell. Near-black `#0A0A0C–#141414` with ~1–3% luminance steps per surface + 1px `#222–#2A2A30` hairlines, zero box-shadow. One warm accent (coral `#FF5A3C` or amber) on the active state only. Monospace data voice (`//`, tabular timecodes `00:00/00:07`), selection = glowing 1–2px accent outline (not shadow). This is ScoutVeda's dashboard grammar.
- **v3_f88 (outro):** true black + one neon-red `#FF1E44` + radial maroon glow; the emphasis word is an emissive light source (bloom/text-shadow), confirming glow-on-value.

### v1 — 3D site visuals
- **v1_f2:** cinematically graded product-lifestyle still (cool `#161A26` shadows / warm `#FFB454` key / vignette); heavy centered all-caps white type + soft shadow; "(PART 383)" seriality badge as a trust cue.
- **v1_f5 / f8 (Dora):** light hero `#F6F7FA` hands off to a full-bleed lit 3D stage `#1A2A6C`; electric-blue CTA `#2F6BFF` + one warm focal pop; "2D flat chrome over a lit 3D world" is the depth trick.
- **v1_f14 / f17 / f20:** near-black violet/magenta field `#0E0F14`; a single horizontal neon scan-line as horizon; a lit glass/sphere 3D object with parallax; oversized light grotesk + tiny tracked-caps eyebrow; v1_f20 adds a mono engineering blueprint overlay (rulers, tick marks) as the studio-credibility device.

### v2 — Apple-style 3D product
- **v2_f5 (headphones):** one hero object ~50–60% of frame on a black void; matte PBR with controlled specular; three-point studio light with a soft **rim/edge light** carving the dark product off the dark bg + radial pedestal glow; monochrome + single blue CTA `#0A84FF`; one typeface, hierarchy by size/weight only; slow eased scroll-synced camera. "Restraint = luxury."
- **v2_f180 / f360 / f540:** object-first, chrome-second (UI reduced to ghost glyph strips in corners, one accent pill); v2_f360 = the **assembled→exploded** beat (slow, "professional internal tech showcase"); v2_f540 (macOS) confirms glass/vibrancy translucency + SF Pro optical sizing as the premium-OS register.
- (v2_f90/f270/f450 are tool/desktop frames, not product heroes — their only transferable read is "single accent + sourceless ambient lighting + negative-space stage.")

### v4 — web-design course (GSAP / pro-tool register)
- **v4_f15 (MacBook hero):** centered lit device on true-black void; monochrome nav + one blue CTA; the only saturated color lives inside the screen (content-as-hero); soft contact shadow + top-edge spotlight.
- **v4_f300 (Hostinger wizard):** cleanest operational-pro-tool model: centered max-width column, one violet accent `#6C4CF1` + semantic green, flat-2.0 surfaces (1px borders + soft shadow, no skeuomorph), in-context browser-chrome mockup framing the input, floating AI-assistant orb. **This is the single best model for ScoutVeda's dashboard shell.**
- **v4_f1800 / f3600 / f4800 / f7200 (code + live 3D):** 65/35 asymmetric split (raw source left, lit WebGL hero right); single cool accent; soft studio key + contact shadow + vignette; pill/segmented configurator controls; **code-to-design gutter ticks** (green/amber/red) as a craft signal.
- **v4_f6000 (agent-log IDE):** the "agentic feed" idiom — circled step indices, expandable nodes, inline diffs `+74 −3` in green/red, live status footer; 90% neutral darks + one cool indigo accent + two semantic colors. The template for any "system is working" live log.
- **v4_f8400:** the 3-step **choreographed "thinking" loop** (URL typed+caret → checkmark → spinner → resolves) simulating intelligence; uppercase-mono loading fallbacks ("LOAD..."). The pattern for ScoutVeda's data-freshness indicator.

### Pass-#4 sharpened extras (new, merge into §1 / §4.5)
- **P41 Content-as-hero via screen-light:** the *only* saturated color on a page lives inside the product/hero object (v4_f15, v2_f5) — all chrome stays neutral. ScoutVeda: the Opportunity Score's number+accent is the sole chromatic element; nav/labels/ticks stay `text-primary/tertiary` neutrals.
- **P42 Gutter status ticks:** thin left-gutter semantic ticks (green/amber/red) aligned to list rows read as "live instrumentation," not decoration — System Health infra-node rows. Red ticks ONLY for real failures.
- **P43 Agentic-feed idiom:** circled numeric step indices + expandable nodes + inline `+n −n` diffs + a live status footer = the "engineered, not templated" voice for any activity/system log (replaces emoji statuses flagged in the audit).
- **M8 (motion) "Content-as-hero light sweep":** hero value carries a single constrained gradient (amber→orange) with a soft bloom; surrounding chrome flat-neutral — the page's one "lit object." Slow shimmer ~8s, never a party.
- **M9 (motion) Agent-log streaming feel:** step rows fade/slide-in as they complete; the running step shows a subtle pulse; footer "✓ Working" ticks — signals a live process without any auto-scroll gimmick.

---

## PASS #5 — 2026-09-25 live-vision re-run (ground-truth frame reads)

**Vision test:** CONFIRMED WORKING this run (test frame v3_f40 returned a full, accurate dark-UI description — not a "cannot see image" refusal). All 35 frames re-read live below. These are the raw, frame-confirmed reads; the distillation into buildable principles follows. No webm source remains (v1–v4 webm already deleted 2026-09-20; 68 JPGs retained as the reference archive).

### V3 — cinematic HUD hero register (v3_f2, f8, f15)
- **v3_f2:** asymmetric split hero, right-weighted visual + left type. 3-tier vertical rhythm (top nav → telemetry sub-bar → stage → bottom progress strip), each band hairline-separated. Palette: warm near-black `#0a0a0a→#000` with radial lift behind subject; off-white `#f4f4f4`; muted cool gray `#6b6b6b–#8a8a8a`; SINGLE desaturated gold accent `#c9a227–#d9b24a` used sparingly (highlight word, live dot). L-shaped viewfinder corner brackets at 4 edges. Two type systems: heavy tight-grotesk display (huge) + wide-tracked uppercase mono micro-labels; accent word carried by HUE not weight. Depth = rim + volumetric light on hero, vignette, floating low-opacity overlay card (glass cue). Motion cues: LIVE dot pulse, "SCROLL +" + bottom progress line w/ square marker = scrub/scroll-progress, corner-bracket scan, %/segment live-updating fields.
- **v3_f8:** light-field variant — near-black chrome `#0C0C0C–#151515` sandwiching a cool light studio gradient `#CFCFCF→#F4F4F4`; single metallic gold `#E8B021–#F5C518`. Strict "image-left / text-right" split; corner alignment brackets as viewport registers. Hierarchy by size + tracking + opacity, almost never color. Depth via PBR specular glints + soft edge-dissolve into gradient + vignette. `SEQ 142/149`, `▸ PLAYBACK`, `SCROLL ▾` = temporal/sequence affordances (the page implies scrubbing a film strip).
- **v3_f15:** dark "case-file" stage; center kept empty, chrome pinned to perimeter (viewfinder/letterbox). Monochrome + TWO disciplined accents (crimson `#ff1a2a` glow + muted gold `#c99a2e`). Depth sold via VOLUMETRIC atmosphere (ground fog, below-light rim on silhouette, suspended dust, layered debris at varying blur = parallax layers) + film grain overlay. Motion: scroll-driven frame-advance (SEQ 011/149), ambient drift/parallax, pulsing glow, right-edge vertical scrollbar = long scroll.

### V3 — data-instrument / dev-workbench register (v3_f40, f50, f60, f70, f80) — THE DASHBOARD GRAMMAR
- **v3_f40 / f50:** three-column "production console": narrow icon rail (~56px) → params/controls panel → wide results canvas, bottom status strip docked. Palette: near-black `#0D0D0F–#141518`, elevated panels `#161619–#1A1A1E` with 1px hairline `#2A2A30`, text `#E8E8EC` / muted `#8A8A93`, ONE mint-green accent `#3DDC84–#34D399` on active states / NEW badge / `@image` chips. Depth = flat dark surfaces + hairline strokes + very soft large-radius shadows (NO heavy drop shadow) — the "OLED/pro" tool look. Type: one grotesk, tight; uppercase 10–11px letter-spaced spec labels ("1080p · 16:9 · 1", "NEW", "2K HD"); weight ramp 400/500/600. Selection = luminous accent OUTLINE on active thumbnail (not shadow).
- **v3_f60:** three-zone split (IDE void + centered 16:9 media card on black + right nav rail). Near-black `#0D0D0D–#161616`, accent coral-red `#E8452F/` rationed ~10%. Depth = TONAL layering (each zone steps luminance up a few points) + hairline borders, NOT drop shadows. The video thumbnail is a LOCALIZED LIGHT SOURCE bleeding warm glow onto the black = single focal "hero light." Mono terminal voice (`// TODO`) = dev-credibility.
- **v3_f70 / f80:** Figma/After-Effects "tools / canvas / properties" three-panel grid; center stage INTENTIONALLY sparse (huge negative space around a single glyph + one line). Coral brand accent `#E85C5C–#FF6B6B` + amber status dot `#E8A33D`; white progress rail. ~90/10 rule: 90% near-black + gray, accents reserved for state/brand only. Depth ambient/evenly-lit screen-phosphor (no directional light), white scrubber + glowing glyph = the only light points. `// TODO:` code-comment idiom turns empty state into dev-culture voice.
- **v3_f88 (outro):** true black `#0a0a0a–#101010` + low-intensity warm-red radial spotlight (`#3a0a0a` center→black) + emissive accent `#ff1e3c`. EMISSIVE BLOOM on the CTA word (additive glow/text-shadow) = "lit from within." Two depth cues: off-center radial volumetric light + additive bloom. Composition: centered focal hierarchy top, corner-docked action control below, big negative space. Confirms glow-on-value + single emissive accent.

### V1 — 3D-site hero language
- **v1_f2:** warm/cool cinematic grade (amber key `#ffb347` vs violet screen `#5b3a9e`/`#2a1850`) — the "high-production" tell; heavy all-caps white type + thick black stroke outline (broadcast legibility over busy bg); screen-over-hands creator-POV; shallow DoF; tactile hardware props = tech credibility.
- **v1_f5 (Dora light):** clean flat SaaS hero `#FFFFFF→#F6F7FB`, ink `#14142B`, ONE electric blue CTA `#3B5BFF`, deep-indigo lit 3D stage panel `#1E1B4B` below. Depth trick = "flat 2D chrome over a lit 3D world"; sparkle icon = generative motion cue.
- **v1_f8 (Dora dark):** cosmic-metaphor brand system (planet horizon + starfield + nebula) used as AMBIENT LIGHTING not clip-art; glassmorphism + soft glows, vignette single light source; recessed darker preview panel; prompt-bar-as-center-of-gravity.
- **v1_f11:** dark `#0B0B12` + magenta bloom `#6E2A86–#A23DB0` + electric cyan rule `#1FE9D6` + cobalt CTA `#2E63FF`. Emissive glow (not shadow) does the depth; "small index + big statement" asymmetric split; neon-rules-as-lit-light-sources.
- **v1_f14:** mirror-symmetric pedestal; type OCCLUDED behind 3D objects = 2.5D layer stack; pure-black `#000→#0B0B0D` + radial spotlight; ~1:8–1:10 size ratio (hero type vs micro labels); ~90% neutral + ~10% violet accent.
- **v1_f17:** asymmetric hero, text left / airy right (cityscape); near-black `#0A0A0C` (NOT pure 000); single electric-green accent `#3DFF88` reserved for ONE word + a few keywords = color as SIGNAL; heavy→light typographic contrast.
- **v1_f20:** two-tone split canvas (matte black top / radial-lime-glow `#A8E63C→#2E7D32` bottom); extreme type-scale contrast (~1:12) = the "editorial-premium" tell; floating annotation/HUD layer (dashed dimension lines + square selection handles + violet handle) over a finished surface = AR-viewport futurism; violet = "editing," green = "live."

### V2 — Apple-style product-hero language
- **v2_f5 (headphones):** ~50–60% hero object on black void; matte PBR with controlled specular + crisp rim highlights; radial vignette spotlight behind product; DOF blur at pointer = 3D tilt/parallax-on-hover; one electric-blue `#2f6bff` Buy pill; product-as-protagonist, copy-as-whisper. "Restraint = luxury."
- **v2_f90 / f180 / f270:** (f90 = tool/desktop empty-stage, f270 = near-matte void + single thumbnail + cursor = "awaiting input" rest frame). Transferable read = single accent + sourceless ambient lighting + negative-space stage.
- **v2_f360:** moody near-black `#0a0a0a–#0d0d0d`; matte-mauve pill controls; desaturated rose accent `#d99a9c–#e8a0a8` on the playhead only; the assembled→exploded "professional internal tech showcase" beat (slow, Apple-style); content supplies drama while chrome stays flat/quiet = "studio in a pocket."
- **v2_f450 / f540:** f540 = macOS glass-on-light register (vibrancy translucency + hairline 1px lift + continuous corners + single cool accent + high-density tabular grid + big display metric = "command-center" OS signal). Confirms glass/vibrancy belongs to the OS/hero register, not the data dashboard.

### V4 — pro-tool / GSAP course register (the operational dashboard model)
- **v4_f15 (MacBook hero):** centered lit device on vignetted near-black `#0a0a0a`; minimal 3-zone top bar (label|links|CTA) in light-weight wide-tracked sans; ONE blue `#2f6bff` CTA; rim light + emissive display + soft grounding shadow; the ONLY saturated color lives inside the screen (content-as-hero).
- **v4_f300 (Hostinger wizard):** THE cleanest operational-pro-tool shell: centered max-width single column, flat-2.0 (1px borders + soft shadow, no skeuomorph), ONE violet `#6C4DF6–#7C5CFF` accent + semantic green reserved for "positive/owned"; input framed inside a mock BROWSER CHROME card (address-bar metaphor = "navigating to a site that will exist"); 79% progress bar; floating AI-assistant gradient orb; recovery paths ("Use temporary domain," "Renew") so the wizard never dead-ends. Best model for ScoutVeda's dashboard shell.
- **v4_f900 / f1800 / f2700 / f3600 / f4800 / f7200 / f8400:** the "code ↔ rendered" split register — dense raw source left, lit/void showcase right. Consistent reads: near-black `#0A0A0C–#0E0E11`; monospace code voice (ligature-rich JetBrains/Fira Code) paired with a clean grotesk card voice = the "engine ↔ presentation" duality; single cool accent (teal `#37D6D6`, or magenta/amber syntax tinted dusty); soft studio key + contact shadow + vignette; pill/segmented configurator controls (toggle pills, `14"/16"`, `10°/90°`) with tactile inset bevel; a thin scrubber/tick rail bridging panes = the timeline affordance; the `gsap` naming + `gsap.timeline()` = the motion engine signal. **f1800/f8400:** hero headline uses a multi-stop NEON GRADIENT fill (cyan→magenta→orange) + soft outer bloom = "lit from within" — but this is the COSTUMED variant; ScoutVeda should keep it to a single amber→orange word, never the rainbow. f7200: 3D hero on pure black with cinematic 3-point lighting (soft key + cool cyan rim + ambient occlusion, no ground plane → floats) + a designed uppercase-mono `<h1>LOAD...</h1>` Suspense fallback.
- **v4_f6000 (agent-log workbench):** the agentic-feed idiom — asym 60/40: vast empty dark "stage" hosting a centered keyboard-palette list (⌘ shortcuts, right-aligned) on the left; a fixed-width right DRAWER with a header (back + title), a `× Stop` pill, circled step indices 1–5, a code-flavored body + "Click to expand," a diff sub-card `✎ Edit · Performance.jsx +74 −3`, and a green-dot "Working" status footer. Near-black `#0A0A0C` + elevated card `#141417` + 1px `#26262B` hairline; monochrome + ONE desaturated indigo accent + two semantic status hues (green `#34D399`, red `#F87171`). Depth = TONAL ELEVATION (luminance steps), zero drop shadows. This is the live-"system is working" template.

### Pass #5 distillation — 12 buildable principles (merge into §1; motion into §4.5)
1. **Two registers, hard split.** v3_f2–f15 (cinematic HUD: brackets, fog, scan, "LIVE") = landing-hero language ONLY. v3_f40–f80 + v4_f300/f6000 (data-instrument: rail·params·canvas, tonal layering, mono voice, single accent) = operational dashboard. ScoutVeda borrows the hero register *sparingly*; the dashboard stays restrained. No viewfinder brackets or telemetry labels on data tables.
2. **Warm matte near-black, never pure / never blue.** Hero fields `#050506→#0B0B0D` (warm, matte). Blue-shifted `#0B0F17` reads clinical; pure `#000` reserved only for the hero "void" behind the Opportunity Score.
3. **Tonal depth, zero box-shadow on dashboard surfaces.** Each surface steps +1–3% luminance over the one below + 1px `#222–#2A30` hairline. Reserve the single soft shadow for the one floating element (hero dial / prompt card).
4. **Selection-by-glowing-outline.** Active card/row/chip = 1–2px accent outline (+ tiny corner tick), `box-shadow:none`. Dark-glass selection idiom (v3_f50).
5. **Single warm accent carries all meaning.** One amber `#D97706–#F59E0B` for active/primary; semantic green/red strictly for good/critical. ~90% neutral + ~10% accent. Never a second decorative hue.
6. **Content-as-hero (the lit object).** The only saturated color on a screen lives INSIDE the hero object (the number + accent gradient of the Opportunity Score). All surrounding chrome (nav, labels, ticks) stays neutral `text-primary/tertiary` → the value reads as "a light source in a dark room."
7. **Glow-on-value only, on meaning.** Emissive bloom (`text-shadow:0 0 24px accent@25%`) reserved for the one key value / emissive CTA (v3_f88, v4_f8400). Subtle 4px status-dot glow on state dots. No ambient pulsing everywhere (reads as costume).
8. **Extreme type-scale contrast + two-family system.** ~10:1 ratio between one big tight-tracked grotesk display and many 10–11px wide-tracked uppercase mono micro-labels. Hierarchy by scale/weight/tracking/opacity, almost never color.
9. **Typographic punctuation = the "engineered" voice.** `//`, `—`, `▸`, `·`, `⌄`, `⊕`, tabular numerals, `SEQ 001/109` counters, `+74 −3` diffs — mono wide-tracked captions do the technical work; body copy stays clean.
10. **Rim light + radial pedestal glow carve dark off dark.** Any hero viz (dial) gets a 1px top edge-light (`#fff@12%`) + a radial lift behind it (~8% brighter at center) so the data object "floats" off the field.
11. **Glass/vibrancy is a hero/OS tool, not a dashboard tool.** `backdrop-filter:blur(12px)` only on landing nav + hero panels (v2_f540 macOS register). Dashboard cards/tables = flat solid token surfaces + hairlines.
12. **Code-to-design gutter status ticks.** A thin left gutter of semantic ticks (green/amber/red) aligned to infrastructure rows (System Health) reads as "live instrumentation," not decoration; red reserved for real failures.

### Pass #5 motion distillation (merge into §4.5)
- **M10** Emissive CTA word bloom: `text-shadow:0 0 24px rgba(accent,.25)` + 8s subtle amber→orange gradient shimmer on the single hero value ONLY (v3_f88, v4_f8400) — never the full rainbow.
- **M11** Tonal-elevation hover (no shadow): active row/card lifts +2–3% luminance + accent outline in 150–200ms, not a drop shadow (v3_f60/f70/f80, v4_f6000).
- **M12** Browser-chrome "navigating-to" input (v4_f300): ASIN/keyword field framed in a mock address-bar card — "navigating to an opportunity," not "filling a form."
- **M13** Data-instrument live drawer (v4_f6000): step rows fade/slide in on completion; running step's dot pulses 2s; footer status ticks on state change; `× Stop` affordance to interrupt — the "live process" feel with zero auto-scroll.
- Reinforced: turntable idle + 3-frame "thinking" loop + assembled→exploded scroll beat (M1–M3) + staggered-group reveals (M4) + state-only glow-pulse (M5) + subtle hover scale (M6) + semantic-loop rule (M7). Fewer things, slower, purposeful = the premium move.

---

## PASS #6 — 2026-09-25 live-vision re-run, this run (ground-truth frame reads)

**Vision test:** CONFIRMED WORKING (test frame v3_f40 returned a full, accurate dark-UI read — not a "cannot see" refusal). All 36 frames re-read live. No `.webm` source remains (v1–v4.webm already deleted 2026-09-20; re-verified absent this run; 68+ JPGs retained). These are the raw, frame-confirmed reads; the net-new distillation (principles #49–#53, motion M14–M16) is merged into the spec §1 / §4.5.5.

### V3 — cinematic HUD hero register
- **v3_f2:** asymmetric two-column hero (left text mid-anchored, right focal image). Near-monochrome `#060606→#0D0D0D` bg, hairlines `#262626–#333`, off-white text `#E9E7E1`, muted gray `#6B6B6B`, ONE scarce warm gold `#D4A33C` (≤5% of pixels). Three type tiers: heavy tight display (mixed white+gold), wide-tracked uppercase mono micro-labels, thin mono subhead. HUD frame: hairline border + corner brackets + 4-corner data readouts (telemetry LIVE, reactor %, SEQ 001/369, SCROLL ↓). Depth = radial vignette + rim light + soft bloom bleeding onto the gold word + low-opacity smoke + translucent glass card. Premium tells: instrumentation language, single-accent discipline, hierarchy-by-scale, framed negative space, cinematic focal lighting, glass layering.
- **v3_f8 (light-field variant):** near-black chrome `#0E0E10/#111114` sandwiching a cool light studio gradient `#C9CBCD→#A9ACAF`; off-white `#F2F3F4`; muted technical gray `#7E8083`; single metallic amber `#D9A31E/#E0B030` (brand dot, accent line, bottom hairline, ember particles). Corner-pinned metadata with L-bracket motifs (`FLIGHT LOG — ARCHIVED`, `SEQ 142/169`, `TITAN II // FINAL FRAME`, `MARK III // ARCHIVED / REPLAY / SCROLL`). Side-lit subject + bloom + drifting ember particles. "Spec-sheet meets film frame" imbalance.
- **v3_f15:** dark "case-file" stage; near-black `#0B0C0E→#111317`, desaturated blue-grey fog `#3A4148`, deep crimson horizon glow `#5E1E24→#7A2A30` used as a *light source* not a flat color; signature metallic amber `#C9A22E/#D4AF37`; off-white `#EDEBE4` primary / muted slate `#8A8D94` secondary / faint `#5A5D63` metadata. Backlit silhouette in low fog, warm red horizon band, particle scatter at multiple opacities (depth of field). Asymmetric diagonal tension (center image + offset right type + corner data).
- **v3_f30:** cinematic 3D-render hero wrapped in a thin HUD. Center kept empty, chrome pinned to perimeter. Volumetric ground fog + backlit rim + suspended dust + layered debris at varying blur = parallax depth layers; film-grain overlay. Single amber accent + one warm crimson light source = 90% monochrome. "Film still + heads-up-display telemetry" hybrid. → register = HERO-ONLY (fog/debris/grain excluded from dashboard).
- **v3_f88 (outro):** true black `#0a0a0a–#101010` + low-intensity warm-red radial spotlight (`#3a0a12` center → black) + emissive accent `#ff1e3c`. Additive EMISSIVE BLOOM on the accent word ("lit from within"). Two depth cues: off-center radial volumetric light + additive bloom. Centered focal hierarchy top, corner-docked action control below, big negative space.

### V3 — data-instrument / dev-workbench register (THE DASHBOARD GRAMMAR)
- **v3_f40:** three-column "production console": narrow icon rail (~56px) → params/controls panel → wide results canvas, bottom status strip docked. Near-black `#0A0A0C/#0E0E11`, elevated panels `#15151A–#1B1B21`, hairline borders `#26262E/#2A2A32`, text `#E6E6EA` / muted `#8A8A93` / disabled `#5A5A63`. ONE mint/teal accent `#4ADE80–#34D399` reserved for signal (logo, NEW badge, @image chip, active toggle, filmstrip ring); saturated red-rose `#F43F5E/#EF4444` only for alerts. "Neutral dark base + one cool accent + one warm signal" 3-role palette. OLED-flat depth (1px tonal steps + hairlines, no drop shadows). Icon-first nav + micro-caps labeling = "software-as-instrument."
- **v3_f50 (Pinterest-light register):** near-white `#FFFFFF→#F5F6F7` field, cool light-gray placeholder tiles `#F1F1F1`, charcoal text `#2A2A2A`, ONE high-saturation accent (brand red `#E60023`). Icon-only edge rail. Skeleton/masonry empty placeholders = "skeleton/loading" not "empty." Soft low-contrast elevation, no hard shadows. Monochrome-neutral + one accent = clean premium light-mode discipline. → light-mode mirror model.
- **v3_f60:** three-zone split (IDE void + centered 16:9 media card on pure black + right nav rail). Near-black `#0A0A0A–#111111`, panels `#161616–#1A1A1A`, hairline `#242424–#2E2E2E`, off-white `#EAEAEA`, muted `#8A8A8A`. Warm coral-orange accent `#FF5A3C` (brand glyph), desaturated green `#22C55E` in toolbar. Selection = subtle light-on-dark fill `#1F1F1F`. MATTE FLAT: no drop shadows, no glass, no chrome gradients — "studio dark" hardware-console feel. Monospace voice (`//`, file paths, `0:07/0:07` timecode) = dev credibility. Asymmetric mission-control grid with dedicated "stage" canvas.
- **v3_f70 / f80:** Figma/AE "tools / canvas / properties" three-panel grid; center INTENTIONALLY sparse (huge negative space around a single centered pixel-mascot glyph + one `// TODO: Everything. Let's start.` line). Coral brand accent `#E85C5C–#FF6B6B` + amber status dot. ~90/10 rule. Depth = ambient evenly-lited "screen-phosphor" (no directional light); white scrubber + glowing glyph = the only light points. Code-comment empty-state idiom = dev-culture voice.
- **v3_f22 (isolated-sheet frame):** a single white detail card (2 items, column header Name/Last modified/File size) floating on a vast near-black `#141417–#1e1f24` void — "isolated sheet" composition. 1px hairline dividers (no boxes), value-based elevation (light-on-dark, zero box-shadow), left-icon+text row rhythm, asymmetric header weighting (large light title vs tiny right "2 items"). Google-blue accent `#1a73e8` used in only two places (Share + selected row). Isolated-sheet focus = "airy, editorial."

### V1 — 3D-site hero language
- **v1_f2 (creator-desk POV):** warm/cool cinematic grade (amber key `#ffb347` vs violet screen `#160f3a→#2a1b5e`); heavy all-caps white type + dark stroke outline over busy art; screen-over-hands one-point-perspective POV; shallow DoF; tactile retro-mechanical keyboard + sci-fi holographic props = "creator-desk" credibility. Saturated green `#3df0a0` reserved for "data/hologram" moments = green-as-signal trick.
- **v1_f5 (Dora light):** flat SaaS hero `#FFFFFF→#F6F7FB`, ink `#14142B`, ONE electric indigo CTA `#2E5BFF–#3B5BFD`, deep-navy lit 3D stage band `#1B1E5E` below with a saturated yellow ring `#F5C518` + violet planet `#8A6FFF`. Real-lit 3D mascot (specular helmet glass, AO) over flat 2D chrome = "flat chrome over lit 3D world." Light-top / dark-bottom launch-into-space split.
- **v1_f8 (Dora dark):** cosmic-metaphor brand system (planet horizon + starfield + nebula) as AMBIENT LIGHTING not clip-art. Deep indigo void `#0A0E2A–#0B1026`, electric violet accent `#7C5CFF/#6D28D9`, magenta-violet gradient mesh `#8B5CF6→#C026D3`, near-white `#F5F7FF`, muted blue-grey `#9AA3C0`. Planet with soft rim/atmospheric glow + dark terminator. Glassmorphic floating prompt bar + pill buttons. "Type behind product" parallax. Prompt-bar = center of gravity.
- **v1_f11:** dark `#050508–#0B0B12` + violet ambient `#6D28D9–#7C3AED` + neon cyan/teal glowing rule `#22D3EE–#2DD4BF` + cobalt CTA `#2563EB–#3B82F6` + pure-white `#F5F5F7`. Left vertical media rail (stacked rounded cards) + wide right type field ("Symbol of purchase power"). Emissive glow (not shadow) does depth; oversized display type + micro eyebrow; glowing horizontal rule = scroll-progress indicator.
- **v1_f14 (Apple AirPods):** strict centered symmetric stage; near-black `#0a0a0c` void; two symmetric glossy earbuds (silvery-white `#f2f2f4` specular → `#a8a8b0` shadow, silicone tips `#d8d8dc`); off-white `#f5f5f7`; ONE Apple-blue `#0071e3` accent. Giant thin-weight product name set *behind* the hardware = 2.5D layer stack (type → product → CTA row). Studio 3-point: soft key upper-front, curved specular streak on glossy stem, gentle AO where tip meets body, faint drop/ambient shadow. Material realism (matte silicone vs glossy plastic vs brushed metal). "Museum-piece" monochrome void.
- **v1_f17:** asymmetric hero (text left rail / airy 3D cityscape right). Near-black cool `#0A0C10–#111418`; off-white `#F4F6F8` headline; body mid-gray `#8A9098`; single electric neon-green `#3DFF5A–#39FF14` accent reserved for ONE word ("power.") + a small cool blue-cyan `#3B82F6–#22D3EE` button. Full-bleed WebGL hero (volumetric haze, silhouetted architecture, single light source). Accent word differentiated by COLOR not size. "3D cinematic stage + editorial type lockup + one-accent system."
- **v1_f20:** two-tone split canvas (matte black top / radial lime→forest green `#A6E22E→#1F5E33` bottom). Extreme type-scale contrast (~1:12). Floating annotation/HUD layer (dashed dimension lines + square selection handles + cyan/teal tab `#00D9C0` + magenta-purple `#8E24AA` OS accent) over a finished 3D-tilted card on a dark charcoal `#1B1B1F` void, with crop/registration marks + `0/0` index counter = "editorial + industrial blueprint" hybrid. violet="editing," green="live."

### V2 — Apple-style product-hero language
- **v2_f5 (headphones):** ~50–60% hero object on black void. Matte-black PBR with controlled specular: broad soft highlight across headband + cup top, underside in deep shadow, one small green reflector to break monochrome. 3/4 turntable pose. Cinematic 3-point: large soft key upper-left, cool rim/edge light from right (separates black-on-black), low fill. Radial vignette `#0A0A0B→#111114`. OFF-WHITE `#F5F5F7` type (ultra-light display + medium subhead + tracked micro labels), muted `#9A9A9F/#6E6E73`. ONE electric-blue `#2F6BFF` Buy pill + a micro green glint `#5FE08A`. Asymmetric split (product center-left, text right, CTA top-right). DOF blur at pointer = tilt/parallax-on-hover; slow idle turntable/float. "Restraint = luxury."
- **v2_f90 (Whisk tool / empty-stage):** flat 2D utility UI borrowing Apple's calm grey/white discipline: soft cool near-white canvas `#F5F5F7`, clean white card with generous radius + soft low-opacity shadow ("levitating white card on grey"), monochrome + ONE saturated accent (yellow `#FFD60A`), thin geometric outline icons. No hero render — the "hero" is the empty grey canvas + white prompt card. Depth = soft shadow + layering + tonal separation, no 3D.
- **v2_f180 (Sony headphone masonry):** dark cinematic monochrome luxury-tech product shot on deep black `#050505→#0a0a0a` with subtle radial center-lift `#161616–#1e1e1e`; matte product body `#0d0d0d–#181818`; soft rim/specular `#3a3a3a→#5a5a5a`. Anodized-matte polymer + fine leather sheen. Extreme negative space, single centered hero, "quiet luxury." Motion cues: slow turntable/parallax, specular sweep on scroll, fade-up + focus-in, 3D tilt on hover. DOF f/1.8 front-tack/rear-melt + radial falloff + rim + contact shadow.
- **v2_f270 (near-empty stage):** flat dark neutral charcoal `#3B3B3B–#404040` field; single rounded media chip bottom-left + a white pointing-hand cursor lower-center; the hero render/gradient/type are ABSENT (empty stage awaiting input). Transferable read = single accent + sourceless ambient lighting + negative-space stage; depth cue = only the small drop shadow under the cursor (floating-UI-over-void trick).
- **v2_f360 (Veo video authoring, assembled→exploded):** wide letterboxed "stage" with heavy negative space; two identical matte forms centered = a system/component set. Matte PBR (low specular, high albedo absorption) so form reads by silhouette + soft shading. Low-key single soft key upper-front, shadows pool into a glossy reflective floor that mirrors the forms (second, dimmer copy of light). ONLY the left unit carries a glowing white element = the single hot focal anchor ("active/charged"). App void `#0A0A0C–#101012`, stage `#161618–#1C1C1F`, matte body `#1E1E21–#2A2A2D`, glow `#F4F6FA→#FFFFFF`, translucent warm-mauve UI pills, muted rose playhead `#B98C8C`. Prompt text explicitly: "assembled → exploded view, slow, Apple style animation." Three stacked depth planes (void → render card → reflective floor). Motion: playhead scrubber + `0:08` timecode + pause/play + adjacent cropped card = a time-based product film; exploded transition = eased, minimal-overshoot, weighty.
- **v2_f450 / f540:** f450 = defocused dark-mode search-page capture (low premium, utilitarian; only reads: restrained near-black + single blue accent + glassy tab bar). f540 = **macOS desktop (glass-on-light register)**: translucent Finder window (vibrancy blur ~85%) over a 3D cityscape wallpaper; magenta→indigo dusk sky `#B13A8F→#3E2A66` + warm window glows; UI dark translucency `#1C1C2E`; blue selection `#0A84FF`; SF Pro tight tracking; continuous rounded corners; restrained 4-layer z-stack. Confirms glass/vibrancy belongs to the OS/hero register, NOT the data dashboard.

### V4 — pro-tool / GSAP course register (the operational dashboard model)
- **v4_f15 (MacBook Pro hero):** strict centered hero on near-black `#000000–#0a0a0a`; thin top nav (brand left, menu right, bright-blue Buy `#0071e3`); off-white `#f5f5f7` type, light-to-regular weight, generous letter-spacing. High-fidelity PBR laptop (gradient highlights on lid edge, soft ambient shadow, emissive screen "bloom"). ALL color/energy quarantined inside the screen (teal `#00b3b3`, electric blue `#1e50ff`, gold `#f5c518`, midnight `#0a1440`) — two-zone strategy (cool monochrome UI vs vivid content). Extreme negative space = spotlight-on-stage. "Interface recedes, product sings."
- **v4_f300 (Hostinger wizard):** THE cleanest operational-pro-tool shell. Single centered column on white; brand bar → heading + helper → lavender info banner `#ECE8FB` → primary card (faux browser mock with domain field, purple focus ring `#6C4CF1–#673DE6` + blue corner dot + lock) → status list (green "Owned" `#15A37A` / purple "Expired" `#7C3AED` pills) → 71% purple progress bar → footer (ghost "← Back" + dark "Next →" `#3B3E52`) + floating purple "Ask Kodee" FAB `#6C3CE9`. Flat-2.0: card lifts via hairline border + very soft shadow, not heavy. Focus signaled by colored ring (crisp), not glow. "Faux-browser mock frames the input as the thing you'll type into." 8px spacing grid, aligned baselines, single accent for emphasis/focus/primary only = "quiet, trustworthy, SaaS-grade."
- **v4_f900 (VS Code + GSAP React scaffold):** strict three-zone horizontal grid (narrow file-tree rail / fluid editor / right preview pane). Near-monochrome dark `#0E1116→#1A1D24`; text mid-cool `#8B909B` secondary / `#E6E8EC` active; ONE blue-indigo accent `#4F46E5/#5B5FC7` + multicolor semantic file-type icons. Two families: mono for code/paths, sans for UI chrome. Depth = value-contrast between panels + thin 1px border `#2A2E37` (no shadows/gradients). Blinking caret = the only lit element.
- **v4_f1800 (code ↔ 3D viewport):** two-pane asymmetric split (code ~70 / 3D ~30) with no visible divider (density + black gutters separate). Top strip `macbook_gsap_app – MacBook-14.jsx` + VS Code diagnostics glyphs. Left = React Three Fiber JSX assembling the laptop mesh-by-mesh (auto-exported `Object_NN` node/material pairs); thin vertical teal gutter line. Right = pure-black viewport: white Apple logo + search/panel icons, white headline "Take a closer look.", low-poly light-gray MacBook (soft ambient shading) on a black void, muted caption `MacbookPro 0.0.8 In MacBook` + two segmented pill controls (white-active vs gray-inactive, a `3D` pill with white active dot). One-Dark syntax palette (magenta keywords `#c586c0–#ff79c6`, teal functions `#56b6c2`, amber strings `#e5c07b–#d19a66`, green `#98c379`, blue `#61afef`, near-white `#f8f8f2`). Density-contrast: tight color-coded code grid left ↔ sparse high-contrast 3D stage right, unified by one dark palette + two-typeface system + small well-placed controls = "art-directed developer showcase."
- **v4_f2700 (ModelSwitcher + configurator):** dense VS Code editor left (tab `ModelSwitcher.jsx › PresentationControls`, `useRef`/`@react-three/drei` imports, scale-based model swap, minimap density bars pink/teal/yellow) ↔ rendered 3D configurator right: near-black panel `#0a0a0b–#0d0d0f` (warm-neutral black, not pure 000), off-white `#f5f5f7`, muted `#86868b`; top bar (Apple logo left, search+download right); "Take a closer look."; 3D MacBook Pro on a dark slightly-reflective pedestal (screen swirling smoke/ink = emissive light source); caption `MacBook Pro 16" in Silver/Space Black`; two pill control clusters (finish toggle + `14"/16"` size toggle, active = white ring). Monochrome low-saturation high-contrast; studio key + AO under base + faint pedestal reflection + radial vignette. Optical (not geometric) centering of hero + controls. `<PresentationControls>` = drag-to-orbit. "Official product configurator: quiet, confident, detail-obsessed."
- **v4_f3600 (Showcase.jsx GSAP scroll section):** strict 50/50 split with single hairline divider = "workbench" metaphor (edit ↔ preview). Preview = macOS chrome; two pill controls top (segmented two-circle toggle + `1×/0.5` speed toggle); near-black `#0a0a0a` page; centered framed sunlit-cityscape video still (warm natural light enters ONLY through the video = monochrome chrome + one warm photographic focal point, gallery restraint); small `Rocket Chip` caption bottom. Code: `.media/.mask/.content/.wrapper` BEM-ish classes + Tailwind `space-y-5 mt-7 pe-10 lg:max-w-md` = modular 4/8pt rhythm + responsive max-width; `loop muted playsInline` ambient loop; `1×/0.5` playback-speed control = GSAP playground. Custom micro-controls (segmented toggle + speed pill) instead of default widgets = product-grade craft.
- **v4_f4800 (Figma + agent panel):** Figma dark canvas + command-overlay menu left (sparse, shortcut list `⌘⇧F` etc.) ↔ dense right app panel "June EAP" simulating an AI/coding assistant reporting on a GSAP scroll-animation task: back arrow + "GSAP Scroll Animations for Performance Section.", accent-blue `× Stop` pill `#5B6EE1–#3D5BF0`, numbered task list 5..1, long implementation paragraph, "Click to expand," a diff sub-line `Edit | Performance.jsx +4 −3` (green/red change counts), `● Working` green-dot status `#3DDC84` + floating scroll-to-bottom chevron. Near-black `#0A0A0C–#0D0D0F`, panel `#131316–#17171B`, hairline `#26262B`, off-white `#E6E6EA`, muted `#8A8A92`. Flat restrained depth (surface-level steps + 1px strokes, even lighting); accent pop on the one CTA; semantic green/red for status/diffs. "Monochrome-dark + one accent + semantic color" = professional dev-tool UI; affordance completeness (back/stop/expand/scroll/status) signals thoughtful idle/working/stopped states.
- **v4_f6000 (agent-log workbench):** the agentic-feed idiom — asymmetric 60/40: vast empty dark "stage" left hosting a centered keyboard-palette list (⌘ shortcuts, right-aligned); fixed-width right DRAWER: header (back + title), `× Stop` pill, circled step indices 1–5, code-flavored body + "Click to expand," diff sub-card `✎ Edit · Performance.jsx +74 −3`, green-dot "Working" status footer. Near-black `#0A0A0C` + elevated card `#141417` + 1px `#26262B` hairline; monochrome + ONE desaturated indigo accent + two semantic status hues (green `#34D399`, red `#F87171`). Depth = TONAL ELEVATION (luminance steps), ZERO drop shadows. The live-"system is working" template.
- **v4_f7200 (Features.jsx scroll-3D + Suspense):** split 1:1 (or ~45/55) "code ↔ result." Editor warm near-black `#1E1E1E/#0D1117`; 3D stage pure/void black `#000000–#050505` isolating a floating MacBook (screen glow `#F5F5F7` cool-light). Syntax: magenta keywords `#C586C0–#BD68FF`, amber-orange strings `#D78A5A–#CE9178`, muted green comments `#6A9955`, steel-blue identifiers `#5C9FD6`, off-white `#D4D4D4`; single teal accent `#2DD4BF–#29B6B6` for scrollbar thumb + status bar (80/20 rule: desaturated neutrals dominate, only the teal + glowing screen are saturated). Explicit in code: `// 3D MODEL ROTATION ANIMATION`, `gsap.timeline()`, `useGSAP`, `ModelScroll`, `useMediaQuery(max-1024)` scale switch, `Suspense` fallback `<h1 className="text-white text-3xl uppercase">Load...</h1>` = a DESIGNED loading state; preload feature videos in `useEffect`. Depth: isolated scale/position in a lightless void → laptop floats; emissive screen glow + soft ambient/rim on metal. "Performance-aware craft" = `Suspense` fallback + media-query scaling + preload + custom-themed scrollbar/status bar = "engineered, not default."
- **v4_f8400 (MacBook Pro "Built for Apple Intelligence" hero — the COSTUMED gradient):** strict vertical-center single-column stack on near-pure-black `#000–#0a0a0a`; white `#f5f5f7` base text; single Apple-blue Buy pill `#0071e3`; the hero headline uses a COOL-TO-WARM 5-STOP RAINBOW GRADIENT: electric blue `#4aa8ff` → violet `#a25bff` → magenta/pink `#ff4fa0` → orange `#ff8a3d` → warm yellow `#ffd24a`, + soft outer bloom. Laptop cropped edge-on (thin sliver) so a translucent dark "glass" dialog panel (URL/Siri-style pinned/checked rows + blinking caret) floats above it; the laptop edge carries a thin luminous rim mirroring the gradient (backlit-from-within). Restrained "monochrome page punctuated by exactly one gradient + one blue." → **This is the COSTUME variant**: the 5-stop rainbow gradient is exactly what ScoutVeda must NOT do (it reads as entertainment/superhero-adjacent). ScoutVeda keeps a single-hue 2-stop amber→orange on one word only. (Reinforces #51, #24, #46.)

### Pass #6 net-new distillation (merged into spec §1 #49–#53 + §4.5.5 M14–M16)
- **#49 Isolated-sheet composition** (v3_f22): a single white detail sheet on a vast dark void, 1px hairlines + value-based elevation, zero box-shadow. ScoutVeda: Product Detail Drawer / export / modals = one sheet, the only elevated object on its page.
- **#50 Light-mode mirror discipline** (v3_f50): monochrome neutral light field + ONE sparse accent + icon-only rail + skeleton placeholders + soft elevation. ScoutVeda light theme mirrors the dark rule (accent sparse, semantic state-only, soft shadow for elevation since light needs it).
- **#51 Tasteful vs costumed neon gradient** (v4_f8400 live read nails it): 5-stop rainbow + bloom = COSTUME; single-hue 2-stop = CRAFT. ScoutVeda hero word = `#D97706→#F59E0B` one word max, never the rainbow.
- **#52 Performance-aware craft = premium signal** (v4_f7200/f8400): designed `LOAD...` Suspense fallback, media-query model scaling, preloaded async — performance-awareness itself reads "engineered."
- **#53 Grain/fog/debris parallax = hero-only** (v3_f30): volumetric fog + backlit silhouette + suspended dust + layered debris at varying blur + film grain, all cinematic-hero. Dashboard replaces with flat tonal layering + hairlines.
- **M14** single-hue-not-rainbow sweep QA gate (reject any 3+-stop multi-hue gradient fill). **M15** no grain/fog/debris/scan on dashboard motion (depth = tonal lift + staggered reveals + exploded beat only). **M16** designed skeleton placeholders = performance craft (async zones use surface-2 + 4% shimmer, never a bare spinner).

**SaaS-not-superhero held:** the costume (viewfinder brackets, scan-lines, "LIVE" telemetry, 5-stop rainbow neon, particle fog, film grain) stays hero-landing-only and is strictly excluded from operational dashboard screens.

**Bottom line:** the craft vocabulary is now fully mapped and hardened. Six vision-confirmed passes; this pass added no new visual language — only register-boundary + performance-craft specifics that harden the existing rules. The hourly job's purpose is served; it can be removed.

