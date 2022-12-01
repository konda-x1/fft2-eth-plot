#version 300 es
#undef lowp
#undef mediump
#undef highp
precision mediump float;

uniform sampler2D texture;

in vec2 texc;

out vec4 color;

vec4 grayToShortRainbow(vec4 grayColor)
{
    if (grayColor.r > 0.75) {
        return vec4(1.0f, (1.0f - grayColor.r) * 4.0f, 0.0f, 1.0f);
    } else if (grayColor.r > 0.5) {
        return vec4((grayColor.r - 0.5f) * 4.0f, 1.0f, 0.0f, 1.0f);
    } else if (grayColor.r > 0.25) {
        return vec4(0.0f, 1.0f, (0.5f - grayColor.r) * 4.0f, 1.0f);
    }
    return vec4(0.0f, grayColor.r * 4.0f, 1.0f, 1.0f);
}

void main(void)
{
    color = grayToShortRainbow(texture2D(texture, texc));
}
