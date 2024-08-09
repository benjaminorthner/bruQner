#version 330 core

#define PI 3.14159265
#define MAX_ANIMATIONS __MAX_ANIMATIONS__

uniform vec2 iResolution;
uniform float iTime;

// SHARED UNIFORMS
uniform int animationCount; // Number of active animations
uniform int animationTypes[MAX_ANIMATIONS]; // 0 for ring, 1 for line, 2 for dotted ring
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
uniform vec2 linePositions[MAX_ANIMATIONS];
uniform float lineLengths[MAX_ANIMATIONS];
uniform float lineAngles[MAX_ANIMATIONS];
uniform float lineThicknesses[MAX_ANIMATIONS];
uniform float lineOpacities[MAX_ANIMATIONS];

// DOTTED RING UNIFORMS
uniform vec3 dotRingColors[MAX_ANIMATIONS];
uniform vec2 dotRingPositions[MAX_ANIMATIONS];
uniform float dotRingSizes[MAX_ANIMATIONS];
uniform float dotRingRadii[MAX_ANIMATIONS];
uniform float dotRingDotCounts[MAX_ANIMATIONS];
uniform float dotRingOpacities[MAX_ANIMATIONS];
uniform float dotRingThicknesses[MAX_ANIMATIONS];
uniform float dotRingAngles[MAX_ANIMATIONS];

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
            float ringAlpha = step(ringRadius - ringThickness, dist) - step(ringRadius, dist);

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
                finalColor = ringColors[i] * currentAlpha;
            }
 
        // Line Animation
        } else if (animationTypes[i] == 1) { 
            vec2 p = uv - linePositions[i];
            float angle = lineAngles[i];
            float len = lineLengths[i];
            float thickness = lineThicknesses[i];
           
            // Calculate the start and end points of the line
            vec2 start = linePositions[i] - vec2(cos(angle), sin(angle)) * len / 2.0;
            vec2 end = linePositions[i] + vec2(cos(angle), sin(angle)) * len / 2.0; 
            // Calculate the distance from the start and end points
            float distStart = length(uv - start);
            float distEnd = length(uv - end);

            // Calculate the perpendicular vector to the line
            vec2 perp = vec2(-sin(angle), cos(angle));
            
            // Calculate the distance from the line
            float dist = abs(dot(p, perp));

            float AA_factor = 0.2;
            float lineAlpha = 
                smoothstep(thickness + thickness*AA_factor, thickness, dist) * ( // width mask
                step(distStart, len / 2.0) + // after-start mask
                step(distEnd, len / 2.0) // after-end mask
                );
            float currentAlpha = lineOpacities[i] * lineAlpha;
            
            if (currentAlpha > maxAlpha) {
                maxAlpha = currentAlpha;
                finalColor = lineColors[i] * currentAlpha;
            }
        
        // Dotted Ring Animation
        } else if (animationTypes[i] == 2) { 
            
            for (int j = 0; j < dotRingDotCounts[i]; j++){
                float theta = j * 2.0 * PI / dotRingDotCounts[i] + dotRingAngles[i];

                vec2 p = uv - dotRingPositions[i] + dotRingRadii[i] * vec2(sin(theta), cos(theta)) ;
                float dist = length(p);
                float ringRadius = dotRingSizes[i];
                float ringThickness = dotRingThicknesses[i];
                float ringAlpha = step(ringRadius - ringThickness, dist) - step(ringRadius, dist);

                float angle = dotRingAngles[i];

                float currentAlpha = dotRingOpacities[i] * ringAlpha;

                if (currentAlpha > maxAlpha) {
                    maxAlpha = currentAlpha;
                    finalColor = dotRingColors[i] * currentAlpha;
                }
            }
        }
    }
    
    fragColor = vec4(clamp(finalColor, 0.0, 1.0), 1.0);
}