import sys
import socket
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
#import pyqtgraph.ptime as ptime
from server_common import *

def complexmodgen(max_mag, np_real_imag_dtype='int16', endian='big'):
    def complexmod(data):
        if type(data) is not bytes:
            raise ValueError(f"data is of type {type(c)}, not {bytes}")
        units = bytes_to_np_array(data, np.dtype(np_real_imag_dtype), '>' if endian == 'big' else '<')
        pairs = units.reshape(-1, 2)
        sqrmodulos = np.sum(np.square(pairs), axis=1)
        scalars = (sqrmodulos / max_mag).clip(0, 1)
        return scalars
    return complexmod

UDP_IP = "127.0.0.1"
UDP_PORT = 4098
IMAGE_SIZE = [256, 8]
PACKET_SIZE = 1026
PACKET_DISCARD_BYTES = 2
UNIT_SIZE = 4 # bytes per data unit
UNIT_INTENSITY_FUNC = complexmodgen(2*16384*16384, 'int16', 'big')

class RAOpenGLWindow( QtGui.QOpenGLWindow ):
    def __init__( self, image_size, render_angle=90, render_num_points=1024 ):
        super().__init__()
        if render_num_points < 2:
            raise ValueError("render_num_points must be at least 2")
        self.angle = render_angle
        self.num_points = render_num_points
        self.profile = QtGui.QOpenGLVersionProfile()
        self.profile.setVersion( 2, 0 )
        
        h, w = image_size
        imat = make_gradient(h, w)
        self.image = QtGui.QImage(imat.data, w, h, w, QtGui.QImage.Format_Grayscale8)#.mirrored()

    def rads(self):
        return np.radians(self.angle)
    
    def intertwine(self, arrs):
        assert len(arrs) > 0
        arr_len = len(arrs[0])
        dimens = len(arrs)
        assert all(len(arr) == arr_len for arr in arrs)
        c = np.empty(dimens * arr_len)
        for i in range(len(arrs)):
            c[i::dimens] = arrs[i]
        return c

    def initializeGL( self ):
        self.gl = self.context().versionFunctions( self.profile )
        
        self.vao_offscreen = QtGui.QOpenGLVertexArrayObject( self )
        self.vao_offscreen.create()
        self.vao = QtGui.QOpenGLVertexArrayObject( self )
        self.vao.create()
        self.texture = QtGui.QOpenGLTexture( self.image, QtGui.QOpenGLTexture.DontGenerateMipMaps )
        self.texture.setWrapMode(QtGui.QOpenGLTexture.ClampToEdge)
        self.texture.setMagnificationFilter(QtGui.QOpenGLTexture.Linear)

        self.program = QtGui.QOpenGLShaderProgram( self )
        self.program.addShaderFromSourceFile( QtGui.QOpenGLShader.Vertex, 'simple_texture.vs' )
        self.program.addShaderFromSourceFile( QtGui.QOpenGLShader.Fragment, 'simple_texture.fs' )
        self.program.link()

        self.program.bind()
        self.matrix = QtGui.QMatrix4x4()
        self.matrix.ortho( 0, 1, 0, 1, 0, 1 )
        self.program.setUniformValue( "mvp", self.matrix )
        self.program.release()

        # screen render
        angles = np.arange(self.num_points) * self.rads() / (self.num_points-1)
        angles_centered = angles + (np.pi - self.rads()) / 2
#        vx = self.intertwine([np.array([0.5] * self.num_points), np.cos(angles_centered) / 2 + 0.5])
        vx = self.intertwine([0.2 * np.cos(angles_centered) / 2 + 0.5, np.cos(angles_centered) / 2 + 0.5])
        vx /= vx.max() - vx.min()
        vx -= vx.min()
#        vy = self.intertwine([np.array([0.5] * self.num_points), np.sin(angles_centered) / 2 + 0.5])
        vy = self.intertwine([0.2 * np.sin(angles_centered) / 2 + 0.5, np.sin(angles_centered) / 2 + 0.5])
        vy /= vy.max() - vy.min()
        vy -= vy.min()
        vz = np.zeros(self.num_points * 2)
        tx = np.repeat(np.linspace(1, 0, self.num_points), 2)
        ty = np.array([0.0, 1.0] * self.num_points)
        self.vertices = self.intertwine([vx, vy, vz])
        self.tex = self.intertwine([tx, ty])
        
        self.vao.bind()
        #self.vertices = [ 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0 ]
        self.vbo_vertices = self.setVertexBuffer( self.vertices, 3, self.program, "position" )
        #self.tex = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
        self.vbo_tex = self.setVertexBuffer( self.tex, 2, self.program, "texCoord" )
        self.vao.release()
        
        self.program.bind()

        self.texture.bind()
        self.vao.bind()
#        self.gl.glClearColor(0.0, 0.125, 0.125, 0.0)
#        self.update()
    
    def resizeGL( self, w, h ):
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)

    def paintGL( self ):
        #self.gl.glViewport( 0, 0, self.image.width(), self.image.height() )

#        self.program.bind()

#        self.texture.bind()
#        self.vao.bind()
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
        self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, self.num_points * 2 )
#        self.vao.release()
#        self.texture.release()

#        self.program.release()
#        self.texture.setData(QtGui.QOpenGLTexture.Luminance, QtGui.QOpenGLTexture.UInt8, np.random.randint(0,255, [256,8]).astype(np.uint8))

    def setVertexBuffer( self, data_array, dim_vertex, program, shader_str ):
        vbo = QtGui.QOpenGLBuffer( QtGui.QOpenGLBuffer.VertexBuffer )
        vbo.create()
        vbo.bind()

        vertices = np.array( data_array, np.float32 )
        vbo.allocate( vertices, vertices.shape[0] * vertices.itemsize )

        attr_loc = program.attributeLocation( shader_str )
        program.enableAttributeArray( attr_loc )
        program.setAttributeBuffer( attr_loc, self.gl.GL_FLOAT, 0, dim_vertex )
        vbo.release()

        return vbo

class MainApp(AbstractApp):
    def __init__(self):
        app = QtWidgets.QApplication( sys.argv )
        window = RAOpenGLWindow(IMAGE_SIZE)
        window.resize( 768, 512 )
        window.setTitle("2D FFT Range-Angle")
        receiver = Receiver(UDP_IP, UDP_PORT, IMAGE_SIZE, PACKET_SIZE, PACKET_DISCARD_BYTES, UNIT_SIZE, UNIT_INTENSITY_FUNC)    
        super().__init__(app, window, receiver)

        #self.updateTime = ptime.time()
        #self.deltas = np.array([])

    def update_data(self):
        if not hasattr(self.window, 'texture'):
            return

        self.window.texture.setData(QtGui.QOpenGLTexture.Luminance, QtGui.QOpenGLTexture.UInt8, self.worker.data)
        self.window.update()

#        now = ptime.time()
#        delta = now - self.updateTime
#        self.updateTime = now
        
#        self.deltas = np.append(self.deltas, [delta])[-1000:]
#        if self.deltas.size == 1000:
#            print(f"{np.mean(self.deltas)*1000:.2f} ms")

if __name__ == '__main__':
    pg.setConfigOption('imageAxisOrder', 'row-major')
    app = MainApp()
    sys.exit(app.run())

