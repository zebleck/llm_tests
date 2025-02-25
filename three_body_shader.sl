// Three-Body Problem (Figure-8 Solution) Shader
// Simulates the classical figure-8 solution with planets and visual effects

// Constants
#define PI 3.14159265359
#define TRAIL_LENGTH 64
#define DT 0.002
#define NUM_STARS 3
#define NUM_SIMULATION_STEPS 3

// State for stars and planets
vec2 starPos[NUM_STARS];
vec2 starVel[NUM_STARS];
vec2 planetPos[NUM_STARS];
vec2 planetVel[NUM_STARS];
vec2 trailPos[NUM_STARS * TRAIL_LENGTH];

// Initial conditions for the figure-8 solution
void initializeSystem(float time) {
    // Figure-8 initial conditions (Chenciner & Montgomery)
    // Apply time offset to create continuous motion
    float t = time * 0.5;
    
    // Parametric figure-8 solution
    float scale = 1.0;
    
    // Star 1
    starPos[0] = scale * vec2(cos(t), sin(t) * cos(t));
    starVel[0] = scale * vec2(-sin(t), cos(t) * cos(t) - sin(t) * sin(t)) * 0.5;
    
    // Star 2 (120 degrees offset)
    float t2 = t + 2.0 * PI / 3.0;
    starPos[1] = scale * vec2(cos(t2), sin(t2) * cos(t2));
    starVel[1] = scale * vec2(-sin(t2), cos(t2) * cos(t2) - sin(t2) * sin(t2)) * 0.5;
    
    // Star 3 (240 degrees offset)
    float t3 = t + 4.0 * PI / 3.0;
    starPos[2] = scale * vec2(cos(t3), sin(t3) * cos(t3));
    starVel[2] = scale * vec2(-sin(t3), cos(t3) * cos(t3) - sin(t3) * sin(t3)) * 0.5;
    
    // Initialize planets at slightly offset positions from their stars
    for (int i = 0; i < NUM_STARS; i++) {
        float angle = time * 2.0 + float(i) * 2.0 * PI / float(NUM_STARS);
        planetPos[i] = starPos[i] + vec2(cos(angle), sin(angle)) * 0.1;
        planetVel[i] = starVel[i] + vec2(-sin(angle), cos(angle)) * 0.3;
    }
    
    // Initialize trail with current positions
    for (int i = 0; i < NUM_STARS; i++) {
        for (int j = 0; j < TRAIL_LENGTH; j++) {
            trailPos[i * TRAIL_LENGTH + j] = starPos[i];
        }
    }
}

// Update system using RK4 integration
void updateSystem() {
    // Store original positions and velocities
    vec2 origPos[NUM_STARS];
    vec2 origVel[NUM_STARS];
    
    for (int i = 0; i < NUM_STARS; i++) {
        origPos[i] = starPos[i];
        origVel[i] = starVel[i];
    }
    
    // Update star positions and velocities using Velocity Verlet integration
    for (int step = 0; step < NUM_SIMULATION_STEPS; step++) {
        // Calculate accelerations at current positions
        vec2 acc[NUM_STARS];
        for (int i = 0; i < NUM_STARS; i++) {
            acc[i] = vec2(0.0, 0.0);
            for (int j = 0; j < NUM_STARS; j++) {
                if (i != j) {
                    vec2 r = starPos[j] - starPos[i];
                    float dist = length(r);
                    acc[i] += 1.0 * normalize(r) / (dist * dist + 0.001);
                }
            }
        }
        
        // Update positions using current velocities
        for (int i = 0; i < NUM_STARS; i++) {
            starPos[i] += starVel[i] * DT + 0.5 * acc[i] * DT * DT;
        }
        
        // Calculate new accelerations at updated positions
        vec2 newAcc[NUM_STARS];
        for (int i = 0; i < NUM_STARS; i++) {
            newAcc[i] = vec2(0.0, 0.0);
            for (int j = 0; j < NUM_STARS; j++) {
                if (i != j) {
                    vec2 r = starPos[j] - starPos[i];
                    float dist = length(r);
                    newAcc[i] += 1.0 * normalize(r) / (dist * dist + 0.001);
                }
            }
        }
        
        // Update velocities using average acceleration
        for (int i = 0; i < NUM_STARS; i++) {
            starVel[i] += 0.5 * (acc[i] + newAcc[i]) * DT;
        }
        
        // Update planets (they just orbit their stars without affecting the system)
        for (int i = 0; i < NUM_STARS; i++) {
            // Simple orbital motion around parent star
            vec2 relPos = planetPos[i] - starPos[i];
            float dist = length(relPos);
            vec2 perpDir = vec2(-relPos.y, relPos.x) / dist;
            
            // Orbital velocity + star's velocity
            vec2 orbitalVel = perpDir * sqrt(0.1 / max(dist, 0.05));
            planetVel[i] = starVel[i] + orbitalVel;
            planetPos[i] += planetVel[i] * DT;
        }
    }
    
    // Update trails (shift all positions)
    for (int i = 0; i < NUM_STARS; i++) {
        for (int j = TRAIL_LENGTH - 1; j > 0; j--) {
            trailPos[i * TRAIL_LENGTH + j] = trailPos[i * TRAIL_LENGTH + j - 1];
        }
        trailPos[i * TRAIL_LENGTH] = starPos[i];
    }
}

// Helper function for star glow - reduced intensity
float starGlow(vec2 uv, vec2 center, float radius, float intensity) {
    float dist = length(uv - center);
    return intensity * exp(-dist * dist / radius);
}

// Gravitational lensing effect
vec2 lensDistortion(vec2 uv) {
    vec2 distortion = vec2(0.0);
    
    for (int i = 0; i < NUM_STARS; i++) {
        vec2 dir = starPos[i] - uv;
        float dist = length(dir);
        float strength = 0.02 / (dist * dist + 0.001);
        distortion += normalize(dir) * strength;
    }
    
    return uv + distortion;
}

// Main rendering function - optimization changes
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / min(iResolution.x, iResolution.y);
    
    // Scale the simulation area
    uv *= 2.0;
    
    // Initialize system with the current time
    float simulationTime = iTime * 0.15;
    
    // Always initialize the system with the current time
    // This will create the illusion of continuous motion
    initializeSystem(simulationTime);
    
    // Run fewer simulation steps to create motion for this frame
    for (int i = 0; i < 3; i++) {  // Reduced from 5
        updateSystem();
    }
    
    // Apply gravitational lensing to background
    vec2 distortedUV = lensDistortion(uv);
    
    // Create a subtle nebula background
    vec3 bgColor = vec3(0.02, 0.03, 0.05);
    float nebula = 0.5 + 0.5 * sin(distortedUV.x * 3.0 + simulationTime) * sin(distortedUV.y * 2.0 - simulationTime * 0.5);
    bgColor += vec3(0.02, 0.01, 0.04) * nebula;
    
    // Space dust effect
    for (int i = 0; i < 20; i++) {
        vec2 dustPos = vec2(
            fract(sin(float(i) * 378.5) * 43758.5453),
            fract(cos(float(i) * 239.3) * 53578.3435)
        ) * 4.0 - 2.0;
        
        // Make dust move slowly in a circular pattern
        dustPos.x += 0.1 * sin(simulationTime * 0.2 + float(i));
        dustPos.y += 0.1 * cos(simulationTime * 0.1 + float(i) * 0.7);
        
        float dust = 0.002 / (length(uv - dustPos) + 0.001);
        bgColor += vec3(0.6, 0.6, 0.8) * dust;
    }
    
    // Initialize color
    vec3 color = bgColor;
    
    // Draw trails
    for (int i = 0; i < NUM_STARS; i++) {
        vec3 trailColor;
        if (i == 0) trailColor = vec3(0.8, 0.2, 0.1);       // Red
        else if (i == 1) trailColor = vec3(0.1, 0.6, 0.8);  // Blue
        else trailColor = vec3(0.8, 0.7, 0.1);              // Yellow
        
        for (int j = 0; j < TRAIL_LENGTH; j++) {
            vec2 pos = trailPos[i * TRAIL_LENGTH + j];
            float fade = 1.0 - float(j) / float(TRAIL_LENGTH);
            float trailSize = 0.005 * fade * fade;
            
            float trail = trailSize / (length(uv - pos) + 0.001);
            color += trailColor * trail * fade;
        }
    }
    
    // Draw planets
    for (int i = 0; i < NUM_STARS; i++) {
        vec3 planetColor;
        if (i == 0) planetColor = vec3(1.0, 0.5, 0.3);      // Orange
        else if (i == 1) planetColor = vec3(0.3, 0.8, 1.0); // Cyan
        else planetColor = vec3(1.0, 0.9, 0.3);             // Light Yellow
        
        float planet = 0.003 / (length(uv - planetPos[i]) + 0.001);
        color += planetColor * planet;
        
        // Planet trail (lighter and shorter)
        vec2 prevPos = planetPos[i] - planetVel[i] * DT * 5.0;
        for (int t = 0; t < 15; t++) {
            float tNorm = float(t) / 15.0;
            vec2 trailPos = mix(planetPos[i], prevPos, tNorm);
            float trailIntensity = 0.002 * (1.0 - tNorm);
            float trail = trailIntensity / (length(uv - trailPos) + 0.001);
            color += planetColor * trail * 0.5;
        }
    }
    
    // Draw stars with reduced glow
    for (int i = 0; i < NUM_STARS; i++) {
        // Calculate star velocity for color modulation
        float vel = length(starVel[i]);
        
        vec3 starColor;
        if (i == 0) starColor = vec3(1.0, 0.4, 0.2);        // Red star
        else if (i == 1) starColor = vec3(0.2, 0.5, 1.0);   // Blue star
        else starColor = vec3(1.0, 0.8, 0.2);               // Yellow star
        
        // Modulate color based on velocity
        starColor = mix(starColor, vec3(1.0), vel * 0.2);
        
        // Basic star shape
        float star = 0.005 / (length(uv - starPos[i]) + 0.001);
        
        // Add glow effect with reduced intensity
        float glow = starGlow(uv, starPos[i], 0.25, 0.05);  // Reduced from 0.3, 0.08
        
        color += starColor * star * 2.0;
        color += starColor * glow;
    }
    
    // Apply some bloom effect
    color = pow(color, vec3(0.8));
    
    // Mouse interaction - create a gravity distortion
    if (iMouse.z > 0.0) {
        vec2 mousePos = (iMouse.xy - 0.5 * iResolution.xy) / min(iResolution.x, iResolution.y) * 2.0;
        float disturbance = 0.02 / (length(uv - mousePos) + 0.01);
        color += vec3(0.5, 0.5, 1.0) * disturbance;
    }
    
    // Output final color
    fragColor = vec4(color, 1.0);
}