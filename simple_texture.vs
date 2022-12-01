#version 300 es

in vec3 position;
in vec2 texCoord;

uniform mat4 mvp;

out vec2 texc;

void main(void)
{
    gl_Position = mvp * vec4(position, 1.0);
    texc = texCoord;
}
