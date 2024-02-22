from dicom import DICOMStudy, DICOMConstants as DC
from annotated import Annotated
from maths import Vec3
import typing as typ

class SurfaceArea:
    def __init__(self, dicomStudy: DICOMStudy, series: int) -> None:
        self.study = dicomStudy

        # Gather point arrays and spacing info
        self.framePoints = []
        self.dz: typ.List[float] = []

        self.frames = dicomStudy.get(series)
        self.aFrames: typ.List[Annotated] = []  # Will speed things up later
        self.pxSpacing: typ.List[typ.List[float]] = []  # Need this info to calculate distance

        self.pointsPerFrame = -1

        for i in range(len(self.frames)):
            frame = self.frames[i]
            annotated = Annotated(frame)
            self.aFrames.append(annotated)
            points = annotated.getPoints()
            if i == 0:
                # First frame
                self.pointsPerFrame = len(points)
            else:
                if (len(points) != self.pointsPerFrame):
                    raise Exception(f"[{DC.uid(frame)}] Points per frame need to be identical ({len(points)} != {self.pointsPerFrame})")
            if i < len(self.frames) - 1:
                self.dz.append(float(DC.get(frame, DC.kSpacingBetweenSlices)))
            
            self.pxSpacing.append([float(t) for t in DC.get(frame, DC.kPixelSpacing)])

        # Actually calculate surface area!
        #### CORE ALGORITHM ####
        self.area: float = 0 # mm^2
        
        for i in range(len(self.aFrames) - 1):
            # Consider this frame and the next one
            currFrame, nextFrame = self.aFrames[i], self.aFrames[i + 1]
            currPts, nextPts = currFrame.getPoints(), nextFrame.getPoints()
            currSpacing, nextSpacing = self.pxSpacing[i], self.pxSpacing[i + 1]
            # Offsets to centers of first pixels (used to calc real distance)
            CIX, CIY, NIX, NIY = currSpacing[1] / 2, currSpacing[0] / 2, nextSpacing[1] / 2, nextSpacing[0] / 2
            # Spacing between pixels
            CSX, CSY, NSX, NSY = currSpacing[1], currSpacing[0], nextSpacing[1], nextSpacing[0]
            for j in range(len(currPts) - 1):
                """
                Consider this point and the next one, in both frames.
                This forms a quadrilateral with 3D coordinates, and
                since our point lists are sorted, we know a correct
                ordering to trace the quadrilateral. Thus we can use
                cross products to find the area:
                """
                currPt1, currPt2, nextPt1, nextPt2 = currPts[j], currPts[j + 1], nextPts[j], nextPts[j + 1]
                # Scale to real distance
                currPt1, currPt2 = (CIX + CSX * currPt1[0], CIY + CSY * currPt1[1]), (CIX + CSX * currPt2[0], CIY + CSY * currPt2[1])
                nextPt1, nextPt2 = (NIX + NSX * nextPt1[0], NIY + NSY * nextPt1[1]), (NIX + NSX * nextPt2[0], NIY + NSY * nextPt2[1])
                a = Vec3(*currPt1, 0)
                b = Vec3(*currPt2, 0)
                c = Vec3(*nextPt2, self.dz[i])
                d = Vec3(*nextPt1, self.dz[i])
                s = 1/2*(a*b + b*c + c*d + d*a)
                self.area += s.mag()
    
    def getArea(self) -> float:
        return self.area
