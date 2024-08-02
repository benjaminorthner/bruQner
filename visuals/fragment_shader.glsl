#version 330 core

#define MAX_ANIMATIONS 30

uniform vec2 iResolution;
uniform float iTime;

// SHARED UNIFORMS
uniform int animationCount; // Number of active animations
uniform int animationTypes[MAX_ANIMATIONS]; // 0 for ring, 1 for line
uniform float animationStartTimes[MAX_ANIMATIONS];

// RING UNIFORMS
uniform vec3 ringColors[MAX_ANIMATIONS];
uniform vec2 ringPositions[MAX_ANIMATIONS];
uniform float ringSizes[MAX_ANIMATIONS];
uniform float ringOpacities[MAX_ANIMATIONS];
uniform float ringThicknesses[MAX_ANIMATIONS];
uniform float rotationSpeeds[MAX_ANIMATIONS];
uniform float armCounts[MAX_ANIMATIONS];

// LINE UNIFORMS
uniform vec3 lineColors[MAX_ANIMATIONS];
uniform float lineThicknesses[MAX_ANIMATIONS];
uniform float lineYPositions[MAX_ANIMATIONS];
uniform float lineOpacities[MAX_ANIMATIONS];

out vec4 fragColor;

void main()
{
    // Convert fragment coordinates to UV coordinates with (0, 0) in the center
    vec2 uv = (gl_FragCoord.xy / iResolution.xy) * 4.0 - 2.0;
    uv.y *= iResolution.y / iResolution.x; // Maintain aspect ratio
    float time = iTime;
    
    vec3 color = vec3(0.0);

    for (int i = 0; i < animationCount; i++) {
        
        // Ring Animation
        if (animationTypes[i] == 0) { 
            
            vec2 p = uv - ringPositions[i];
            float dist = length(p);
            float ringRadius = ringSizes[i];
            float ringThickness = ringThicknesses[i];
            float ringAlpha = step(ringRadius - ringThickness, dist) - step(ringRadius + ringThickness, dist);

            // pinwheel ring
            float angle = atan(p.y, p.x) + 0.2 * time * rotationSpeeds[i];
            float arm_count = armCounts[i];

            float pinwheelAlpha = 1;
            if (arm_count > 1) {
                pinwheelAlpha = step(0.5 + 0.5* sin(arm_count * angle + 0.2 * time * rotationSpeeds[i]), 0.5);
            }

            color += ringColors[i] * ringOpacities[i] * ringAlpha * pinwheelAlpha;
 
        // Line Animation
        } else if (animationTypes[i] == 1) { 
            float lineTime = time - animationStartTimes[i];
            float y = uv.y - lineYPositions[i];
            float thickness = lineThicknesses[i];
            float alpha = step(- thickness / 2.0, y) - step(thickness / 2.0, y); 
            color += lineColors[i] * lineOpacities[i] * alpha;
        }
    }
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
