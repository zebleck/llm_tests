// Spacetime Fabric Simulation
// A shader that visualizes spacetime as a dynamic, elastic fabric

// Constants for physics simulation
#define MAX_MASSES 5
#define ELASTICITY 0.3
#define DAMPING 0.97
#define PROPAGATION_SPEED 0.2
#define MEMORY_DECAY 0.985
#define LIGHT_SPEED 0.8
#define TEAR_THRESHOLD 2.0
#define TEAR_HEAL_RATE 0.05
#define SINGULARITY_THRESHOLD 5.0

// Buffers:
// Buffer A: Displacement field (xy) and velocity (zw)
// Buffer B: Light particles positions and directions
// Buffer C: Masses information (position, velocity, mass)

// Common uniforms
uniform float iTime;
uniform vec2 iResolution;
uniform vec2 iMouse;
uniform sampler2D iChannel0; // Previous frame displacement
uniform sampler2D iChannel1; // Light particles
uniform sampler2D iChannel2; // Masses information
uniform sampler2D iChannel3; // Noise texture for randomness

// Mass structure (in buffer C)
// x, y: position
// z: mass
// w: velocity magnitude

// Buffer A: Spacetime fabric simulation
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;
    
    // Read current state
    vec4 current = texture(iChannel0, uv);
    vec2 displacement = current.xy;
    vec2 velocity = current.zw;
    
    // Read neighboring cells for propagation
    vec4 left = texture(iChannel0, uv - vec2(texel.x, 0.0));
    vec4 right = texture(iChannel0, uv + vec2(texel.x, 0.0));
    vec4 up = texture(iChannel0, uv - vec2(0.0, texel.y));
    vec4 down = texture(iChannel0, uv + vec2(0.0, texel.y));
    
    // Calculate Laplacian (sum of neighbors - 4 * center)
    vec2 laplacian = left.xy + right.xy + up.xy + down.xy - 4.0 * displacement;
    
    // Apply wave equation: acceleration = c² * laplacian
    vec2 acceleration = PROPAGATION_SPEED * PROPAGATION_SPEED * laplacian;
    
    // Apply forces from masses
    for (int i = 0; i < MAX_MASSES; i++) {
        // Read mass data
        vec4 massData = texelFetch(iChannel2, ivec2(i, 0), 0);
        if (massData.z <= 0.0) continue; // Skip inactive masses
        
        vec2 massPos = massData.xy;
        float mass = massData.z;
        vec2 massVel = massData.w * normalize(texelFetch(iChannel2, ivec2(i, 1), 0).xy);
        
        // Calculate distance to mass
        vec2 pixelPos = uv * iResolution.xy;
        vec2 delta = pixelPos - massPos;
        float dist = length(delta);
        
        // Gravitational well effect
        float force = -mass / max(dist, 10.0);
        acceleration += normalize(delta) * force;
        
        // Wake effect from moving masses
        float wake = mass * length(massVel) * exp(-0.01 * dist);
        vec2 wakeDir = normalize(vec2(massVel.y, -massVel.x));
        float wakePhase = dot(normalize(delta), wakeDir) * dist * 0.05;
        acceleration += wakeDir * wake * sin(wakePhase + iTime * 2.0);
    }
    
    // Mouse interaction
    if (iMouse.z > 0.0) {
        vec2 mousePos = iMouse.xy;
        vec2 delta = fragCoord - mousePos;
        float dist = length(delta);
        float force = -5.0 / max(dist, 5.0);
        acceleration += normalize(delta) * force;
    }
    
    // Update velocity with acceleration
    velocity += acceleration;
    
    // Apply damping
    velocity *= DAMPING;
    
    // Update displacement with velocity
    displacement += velocity;
    
    // Apply memory decay
    displacement *= MEMORY_DECAY;
    
    // Check for tears in spacetime
    float strain = length(laplacian);
    if (strain > TEAR_THRESHOLD) {
        // Create visual tear effect
        float tearNoise = texture(iChannel3, uv + iTime * 0.01).x;
        displacement += (tearNoise - 0.5) * 0.5;
        
        // Heal tears over time
        velocity *= 0.7; // Dampen more at tears
    }
    
    // Check for singularity formation
    float deformation = length(displacement);
    if (deformation > SINGULARITY_THRESHOLD) {
        // Create singularity effect
        float angle = atan(displacement.y, displacement.x) + iTime;
        displacement = SINGULARITY_THRESHOLD * vec2(cos(angle), sin(angle));
        velocity *= 0.5; // Slow down at singularity
    }
    
    // Output updated state
    fragColor = vec4(displacement, velocity);
}

// Buffer B: Light particles simulation
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    
    // Read current light particle state
    vec4 particle = texture(iChannel1, uv);
    
    // Initialize new particles at the edges
    if (particle.w < 0.1 || particle.z < 0.1) {
        // Randomly spawn new particles
        float rand = texture(iChannel3, uv + iTime * 0.1).x;
        if (rand > 0.99) {
            // Determine spawn position at the edge
            float edgePos = texture(iChannel3, uv + vec2(0.3, 0.7)).y;
            vec2 pos, dir;
            
            if (uv.x < 0.1) {
                // Left edge
                pos = vec2(0.0, edgePos);
                dir = vec2(1.0, (rand - 0.5) * 0.2);
            } else if (uv.x > 0.9) {
                // Right edge
                pos = vec2(1.0, edgePos);
                dir = vec2(-1.0, (rand - 0.5) * 0.2);
            } else if (uv.y < 0.1) {
                // Bottom edge
                pos = vec2(edgePos, 0.0);
                dir = vec2((rand - 0.5) * 0.2, 1.0);
            } else {
                // Top edge
                pos = vec2(edgePos, 1.0);
                dir = vec2((rand - 0.5) * 0.2, -1.0);
            }
            
            // Initialize new particle
            particle = vec4(pos, 1.0, 1.0); // Position (xy), direction angle (z), active flag (w)
        }
    }
    
    // Skip inactive particles
    if (particle.w < 0.5) {
        fragColor = particle;
        return;
    }
    
    // Get current position and extract direction
    vec2 pos = particle.xy;
    float angle = particle.z;
    vec2 dir = vec2(cos(angle), sin(angle));
    
    // Sample spacetime displacement at current position
    vec2 displacement = texture(iChannel0, pos).xy;
    
    // Calculate curvature effect on light direction
    float curvatureStrength = length(displacement) * 2.0;
    vec2 curvatureDir = normalize(displacement);
    
    // Apply quantum effects (probabilistic jumps)
    float quantumRand = texture(iChannel3, pos + iTime * 0.05).x;
    if (quantumRand > 0.98) {
        // Quantum jump
        dir = normalize(dir + (texture(iChannel3, pos + vec2(0.1, 0.2)).xy - 0.5) * 0.5);
        angle = atan(dir.y, dir.x);
    } else {
        // Normal bending of light
        dir = normalize(dir + curvatureDir * curvatureStrength * 0.05);
        angle = atan(dir.y, dir.x);
    }
    
    // Move particle
    pos += dir * LIGHT_SPEED * 0.01;
    
    // Check if particle is still in bounds
    if (pos.x < 0.0 || pos.x > 1.0 || pos.y < 0.0 || pos.y > 1.0) {
        // Deactivate particle
        particle.w = 0.0;
    } else {
        // Update particle state
        particle = vec4(pos, angle, 1.0);
    }
    
    fragColor = particle;
}

// Buffer C: Masses simulation
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 pixel = ivec2(fragCoord);
    
    // First row contains positions and masses
    // Second row contains velocity directions
    
    if (pixel.y == 0) {
        // Position and mass data
        if (pixel.x < MAX_MASSES) {
            vec4 massData = texelFetch(iChannel2, ivec2(pixel.x, 0), 0);
            
            // Initialize masses if needed
            if (iFrame < 10) {
                if (pixel.x == 0) {
                    // Central large mass
                    massData = vec4(iResolution.xy * 0.5, 3.0, 0.0);
                } else if (pixel.x < MAX_MASSES) {
                    // Smaller orbiting masses
                    float angle = float(pixel.x) * 1.25;
                    float dist = 100.0 + float(pixel.x) * 50.0;
                    vec2 pos = iResolution.xy * 0.5 + dist * vec2(cos(angle), sin(angle));
                    float mass = 0.5 + float(pixel.x) * 0.3;
                    float speed = 1.0 + float(pixel.x) * 0.2;
                    massData = vec4(pos, mass, speed);
                }
            } else {
                // Update mass position based on physics
                vec2 pos = massData.xy;
                float mass = massData.z;
                float speed = massData.w;
                
                if (mass > 0.0) {
                    // Get velocity direction
                    vec2 velDir = texelFetch(iChannel2, ivec2(pixel.x, 1), 0).xy;
                    
                    // Calculate gravitational forces from other masses
                    vec2 acceleration = vec2(0.0);
                    for (int i = 0; i < MAX_MASSES; i++) {
                        if (i != pixel.x) {
                            vec4 otherMass = texelFetch(iChannel2, ivec2(i, 0), 0);
                            if (otherMass.z > 0.0) {
                                vec2 delta = otherMass.xy - pos;
                                float dist = length(delta);
                                if (dist > 5.0) {
                                    float force = otherMass.z / (dist * dist);
                                    acceleration += normalize(delta) * force;
                                }
                            }
                        }
                    }
                    
                    // Update velocity direction
                    velDir = normalize(velDir + acceleration * 0.01);
                    texelFetch(iChannel2, ivec2(pixel.x, 1), 0) = vec4(velDir, 0.0, 0.0);
                    
                    // Update position
                    pos += velDir * speed;
                    
                    // Bounce off edges
                    if (pos.x < 50.0 || pos.x > iResolution.x - 50.0) {
                        velDir.x = -velDir.x;
                        pos.x = clamp(pos.x, 50.0, iResolution.x - 50.0);
                    }
                    if (pos.y < 50.0 || pos.y > iResolution.y - 50.0) {
                        velDir.y = -velDir.y;
                        pos.y = clamp(pos.y, 50.0, iResolution.y - 50.0);
                    }
                    
                    // Update mass data
                    massData = vec4(pos, mass, speed);
                    
                    // Store updated velocity direction
                    texelFetch(iChannel2, ivec2(pixel.x, 1), 0) = vec4(velDir, 0.0, 0.0);
                }
            }
            
            fragColor = massData;
        } else {
            discard;
        }
    } else if (pixel.y == 1) {
        // Velocity direction data
        if (pixel.x < MAX_MASSES) {
            vec4 velData = texelFetch(iChannel2, ivec2(pixel.x, 1), 0);
            
            // Initialize velocity directions if needed
            if (iFrame < 10) {
                if (pixel.x == 0) {
                    // Central mass doesn't move
                    velData = vec4(0.0, 0.0, 0.0, 0.0);
                } else {
                    // Orbiting masses get perpendicular velocity to create orbit
                    vec4 massData = texelFetch(iChannel2, ivec2(pixel.x, 0), 0);
                    vec2 toCenter = iResolution.xy * 0.5 - massData.xy;
                    velData = vec4(normalize(vec2(-toCenter.y, toCenter.x)), 0.0, 0.0);
                }
            }
            
            fragColor = velData;
        } else {
            discard;
        }
    } else {
        discard;
    }
}

// Main rendering pass
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    
    // Sample displacement field
    vec2 displacement = texture(iChannel0, uv).xy;
    float deformation = length(displacement);
    
    // Base color based on deformation
    vec3 color = mix(
        vec3(0.0, 0.05, 0.2),  // Deep space color
        vec3(0.3, 0.4, 0.8),   // Deformed space color
        smoothstep(0.0, 1.0, deformation)
    );
    
    // Add grid pattern to visualize the fabric
    vec2 gridUV = (uv + displacement * 0.1) * 20.0;
    vec2 gridFrac = fract(gridUV);
    float grid = smoothstep(0.03, 0.0, min(gridFrac.x, gridFrac.y));
    color = mix(color, vec3(0.5, 0.7, 1.0), grid * 0.2);
    
    // Visualize tears in spacetime
    float strain = length(displacement - texture(iChannel0, uv + vec2(1.0/iResolution.x, 0.0)).xy);
    if (strain > TEAR_THRESHOLD * 0.5) {
        float tearIntensity = smoothstep(TEAR_THRESHOLD * 0.5, TEAR_THRESHOLD, strain);
        color = mix(color, vec3(1.0, 0.3, 0.1), tearIntensity * 0.7);
    }
    
    // Visualize singularities
    if (deformation > SINGULARITY_THRESHOLD * 0.8) {
        float singularityIntensity = smoothstep(SINGULARITY_THRESHOLD * 0.8, SINGULARITY_THRESHOLD, deformation);
        color = mix(color, vec3(0.0, 0.0, 0.0), singularityIntensity);
        
        // Add event horizon glow
        float glow = smoothstep(SINGULARITY_THRESHOLD * 0.9, SINGULARITY_THRESHOLD * 0.8, deformation);
        color += vec3(1.0, 0.5, 0.0) * glow * 0.5;
    }
    
    // Render masses
    for (int i = 0; i < MAX_MASSES; i++) {
        vec4 massData = texelFetch(iChannel2, ivec2(i, 0), 0);
        if (massData.z > 0.0) {
            vec2 massPos = massData.xy / iResolution.xy;
            float dist = length(uv - massPos);
            float massSize = 0.01 * sqrt(massData.z);
            
            if (dist < massSize) {
                float intensity = smoothstep(massSize, 0.0, dist);
                color = mix(color, vec3(1.0, 0.9, 0.5), intensity);
            }
            
            // Add glow around masses
            float glow = 0.02 * massData.z / (dist * dist * 100.0);
            color += vec3(1.0, 0.7, 0.3) * glow;
        }
    }
    
    // Render light particles
    for (int y = 0; y < int(iResolution.y); y += 10) {
        for (int x = 0; x < int(iResolution.x); x += 10) {
            vec4 particle = texelFetch(iChannel1, ivec2(x, y), 0);
            if (particle.w > 0.5) {
                vec2 particlePos = particle.xy;
                float dist = length(uv - particlePos);
                
                if (dist < 0.005) {
                    float intensity = smoothstep(0.005, 0.0, dist);
                    color = mix(color, vec3(1.0), intensity);
                }
                
                // Add trail
                vec2 dir = vec2(cos(particle.z), sin(particle.z));
                float trailDist = length(uv - particlePos + dir * 0.01);
                float trail = 0.001 / (trailDist * trailDist);
                color += vec3(0.8, 0.9, 1.0) * trail;
            }
        }
    }
    
    // Add subtle bloom effect
    vec3 bloom = vec3(0.0);
    for (float i = 0.0; i < 5.0; i++) {
        float offset = i * 0.01;
        bloom += texture(iChannel0, uv + vec2(offset, 0.0)).xyz;
        bloom += texture(iChannel0, uv - vec2(offset, 0.0)).xyz;
        bloom += texture(iChannel0, uv + vec2(0.0, offset)).xyz;
        bloom += texture(iChannel0, uv - vec2(0.0, offset)).xyz;
    }
    bloom *= 0.05 * vec3(0.5, 0.7, 1.0);
    color += bloom;
    
    // Final color adjustment
    color = pow(color, vec3(0.8)); // Gamma correction
    
    fragColor = vec4(color, 1.0);
}