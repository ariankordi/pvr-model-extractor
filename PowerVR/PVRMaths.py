# A unfinished port of PVRMaths.js from Imagination Technologies's WebGL_SDK to fix animation support for PODS.

import array
import numpy
import math

class PVRMaths:
    # PVRVector3 functions
    def PVRVector3(x,y,z):
        data = []
        if x != None:
            data[0] = x
        if y != None:
            data[1] = y
        if z != None:
            data[2] = x
        return(data)
    # PVRVector3.linearInterpolate
    def PVRVector3LI(a,b,f):
        v = PVRVector3()
        v[0] = a[0] + ((b[0] - a[0]) * f)
        v[1] = a[1] + ((b[1] - a[1]) * f)
        v[0] = a[2] + ((b[2] - a[2]) * f)
        return values
    # PVRVector3.add
    def PVRVector3Add(lhs,rhs):
        v = PVRVector3()
        v[0] = lhs[0] + rhs[0]
        v[1] = lhs[1] + rhs[1]
        v[2] = lhs[2] + rhs[2]
        return v
    # PVRVector3.subtract
    def PVRVector3Minus(lhs,rhs):
        v = PVRVector3()
        v[0] = lhs[0] - rhs[0]
        v[1] = lhs[1] - rhs[1]
        v[2] = lhs[2] - rhs[2]
        return v
    # PVRVector3.dot
    def PVRVector3Dot(lhs,rhs):
        v = lhs[0] * rhs[0] + lhs[1] * rhs[1] + lhs[2] * rhs[2]
        return v
    # PVRVector3.matrixMultiply
    def PVRVector3MMultiply(lhs,rhs):
        v = PVRVector3()
        v[0] = lhs[0] * rhs[0] + lhs[1] * rhs[1] + lhs[2] * rhs[2]
        v[1] = lhs[0] * rhs[4] + lhs[1] * rhs[5] + lhs[2] * rhs[6]
        v[2] = lhs[0] * rhs[8] + lhs[1] * rhs[9] + lhs[2] * rhs[10]
        return v
    # PVRVector3.cross
    def PVRVector3Cross(lhs,rhs):
        v = PVRVector3()
        v[0] = lhs[1] * rhs[2] - lhs[2] * rhs[1]
        v[1] = lhs[2] * rhs[0] - lhs[0] * rhs[2]
        v[2] = lhs[0] * rhs[1] - lhs[1] * rhs[0]
        return v
    # PVRVector3.scalarMultiply
    def PVRVector3SMultiply(a, s):
        v = PVRVector3()
        v[0] = a[0] * s
        v[1] = a[1] * s
        v[2] = a[2] * s
        return v
    # PVRVector3.scalarAdd
    def PVRVector3SAdd(a, s):
        v = PVRVector3()
        v[0] = a[0] + s
        v[1] = a[1] + s
        v[2] = a[2] + s
        return v
    
    # PVRMatrix4x4 functions
    def PVRMatrix4x4():
        data = numpy.zeros(16)
        return data
    # PVRVector4x4.identity
    def PVRVector4x4Iden():
        m = PVRVector4x4()
        m[0] = 1.0
        m[4] = 0.0
        m[8]  = 0.0
        m[12] = 0.0
        m[1] = 0.0
        m[5] = 1.0
        m[9]  = 0.0
        m[13] = 0.0
        m[2] = 0.0
        m[6] = 0.0 
        m[10] = 1.0
        m[14] = 0.0
        m[3] = 0.0
        m[7] = 0.0
        m[11] = 0.0
        m[15] = 1.0
        return m
    # PVRVector4x4.createTranslation3D
    def PVRVector4x4T3D(x,y,z):
        m = PVRVector4x4Iden()
        # Handle 3x floats as input (Mainly because I don't have time!)
        m[12] = x
        m[13] = y
        m[14] = z

        return m
    # PVRVector4x4.createRotationX3D
    def PVRVector4x4RX3D(angle):
        m = PVRVector4x4Iden()
        m3 = PVRVector3x3RX3D(angle)
        
        m.data[0]  = m3.data[0]
        m.data[1]  = m3.data[1]
        m.data[2]  = m3.data[2]
        m.data[4]  = m3.data[3]
        m.data[5]  = m3.data[4]
        m.data[6]  = m3.data[5]
        m.data[8]  = m3.data[6]
        m.data[9]  = m3.data[7]
        m.data[10] = m3.data[8]

        return m
    # PVRVector4x4.createRotationY3D
    def PVRVector4x4RY3D(angle):
        m = PVRVector4x4Iden()
        m3 = PVRVector3x3RY3D(angle)
        
        m.data[0]  = m3.data[0]
        m.data[1]  = m3.data[1]
        m.data[2]  = m3.data[2]
        m.data[4]  = m3.data[3]
        m.data[5]  = m3.data[4]
        m.data[6]  = m3.data[5]
        m.data[8]  = m3.data[6]
        m.data[9]  = m3.data[7]
        m.data[10] = m3.data[8]

        return m
    # PVRVector4x4.createRotationY3D
    def PVRVector4x4RZ3D(angle):
        m = PVRVector4x4Iden()
        m3 = PVRVector3x3RZ3D(angle)
        
        m.data[0]  = m3.data[0]
        m.data[1]  = m3.data[1]
        m.data[2]  = m3.data[2]
        m.data[4]  = m3.data[3]
        m.data[5]  = m3.data[4]
        m.data[6]  = m3.data[5]
        m.data[8]  = m3.data[6]
        m.data[9]  = m3.data[7]
        m.data[10] = m3.data[8]

        return m
    
    # PVRMatrix3x3 functions
    def PVRVector3x3():
        data = numpy.zeros(9)
        return data
    # PVRVector3x3.identity
    def PVRVector3x3Iden():
        m = PVRVector3x3()
        m.data[0] = 1.0  
        m.data[3] = 0.0  
        m.data[6]  = 0.0
        m.data[1] = 0.0  
        m.data[4] = 1.0  
        m.data[7]  = 0.0
        m.data[2] = 0.0  
        m.data[5] = 0.0  
        m.data[8]  = 1.0
        return m
    # PVRVector3x3.createRotationX3D
    def PVRVector3x3RX3D(radians):
        m = PVRVector3x3Iden()

        cosineX = math.cos(radians)
        sineX = math.sin(radians)

        m[4] = cosineX
        m[5] = -sineX
        m[7] = sineX
        m[8] = cosineX
    
        return m
    # PVRVector3x3.createRotationY3D
    def PVRVector3x3RY3D(radians):
        m = PVRVector3x3Iden()

        cosineY = math.cos(radians)
        sineY = math.sin(radians)

        m[0] = cosineY
        m[2] = -sineY
        m[6] = sineY
        m[8] = cosineY
    
        return m
    # PVRVector3x3.createRotationz3D
    def PVRVector3x3RZ3D(radians):
        m = PVRVector3x3Iden()

        cosineZ = math.cos(radians)
        sineZ = math.sin(radians)

        m[0] = cosineZ
        m[1] = -sineZ
        m[3] = sineZ
        m[4] = cosineZ
    
        return m