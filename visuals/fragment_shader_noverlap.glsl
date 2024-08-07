#version 330 core

#define MAX_ANIMATIONS __MAX_ANIMATIONS__

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
    
    vec3 finalColor = vec3(0.0);
    float maxAlpha = 0.0;  // Track the maximum alpha value

    // Iterate through animations in reverse order
    for (int i = animationCount - 1; i >= 0; i--) {
        
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

            float currentAlpha = ringOpacities[i] * ringAlpha * pinwheelAlpha;

            if (currentAlpha > maxAlpha) {
                maxAlpha = currentAlpha;
                finalColor = ringColors[i] * ringOpacities[i];
            }
 
        // Line Animation
        } else if (animationTypes[i] == 1) { 
            float lineTime = time - animationStartTimes[i];
            float y = uv.y - lineYPositions[i];
            float thickness = lineThicknesses[i];
            float alpha = step(- thickness / 2.0, y) - step(thickness / 2.0, y); 
            float currentAlpha = lineOpacities[i] * alpha;

            if (currentAlpha > maxAlpha) {
                maxAlpha = currentAlpha;
                finalColor = lineColors[i];
            }
        }
    }
    
    fragColor = vec4(clamp(finalColor, 0.0, 1.0), 1.0);
}