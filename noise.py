import time
from pymclevel import alphaMaterials
import numpy as np
import math

displayName = "Noise Replace"

inputs = (
    ("Find except?", True),
    ("Find:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("Scale:", 8.0),
    ("Octaves:", (1, 1, 20)),
    ("Proportion:", 0.4),
    ("Scale controls the general size of the fluctations, octaves significantly increase the chaos (would recommend <3 (aww)), proportion is the roouuughly the percentage of blocks replaced.", "label"),
)


def coserp(a, b, x): # im making it a thing.
    f = (1.0 - math.cos(math.pi * x)) * 0.5
    return a*(1.0 - f) + b*f


# Bit of an odd perlin implementation mostly because i dont actually think its
# perlin at all lmao. I kinda just took the idea of perlin and ran w it a bit
# since ngl i still dont fully understand the concept of perlin noise. This
# works quite well for this filters applications tho, so just dont use it
# anywhere but here :)
class Perlin:
    def __init__(self, box, scale, octave):
        self.scale = scale
        self.octave = octave
        width  = int((box.width  - 1) / scale) + 2 # x
        height = int((box.height - 1) / scale) + 2 # y
        length = int((box.length - 1) / scale) + 2 # z
        self.nodes = np.random.rand(width, height, length)

        if self.octave > 1:
            self.next = Perlin(box, scale*0.5, octave - 1)



    def interpolate(self, x1, y1, z1, x2, y2, z2, px, py, pz):
        return coserp(
            coserp(
                coserp(self.nodes[x1,y1,z1], self.nodes[x2,y1,z1], px),
                coserp(self.nodes[x1,y2,z1], self.nodes[x2,y2,z1], px),
                py
            ),
            coserp(
                coserp(self.nodes[x1,y1,z2], self.nodes[x2,y1,z2], px),
                coserp(self.nodes[x1,y2,z2], self.nodes[x2,y2,z2], px),
                py
            ),
            pz
        )


    def __call__(self, x, y, z):
        # Get the proportion this coord is from the prev node to the next.
        px = (x % self.scale) / self.scale
        py = (y % self.scale) / self.scale
        pz = (z % self.scale) / self.scale

        # Scale coords to node indices.
        nx = (int)(x / self.scale)
        ny = (int)(y / self.scale)
        nz = (int)(z / self.scale)

        ret = self.interpolate(nx, ny, nz, nx+1, ny+1, nz+1, px, py, pz)

        if self.octave > 1:
            ret += 0.5 * self.next(x, y, z)
            ret /= 1.5

        return ret


def matches(is_except, block, level, x, y, z):
    level_block = (level.blockAt(x,y,z), level.blockDataAt(x,y,z))
    if is_except:
        return block != level_block
    else:
        return block == level_block



def perform(level, box, options):
    start = time.time()
    np.random.seed()

    # Get the noise options and create the generator.
    scale = options["Scale:"]
    octaves = options["Octaves:"]
    proportion = options["Proportion:"]
    perlin = Perlin(box, scale, octaves)

    if proportion <= 0:
        raise Exception("Cannot have a negative proportion buddy.")

    print("Scale: {}".format(scale))
    print("Octaves: {}".format(octaves))
    print("Proportion: {}".format(proportion))


    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    find_except = options["Find except?"]
    find_block = (options["Find:"].ID, options["Find:"].blockData)

    # Pridee colours for testing.
    # woolid = np.array([0, 8, 7, 15, 12, 14, 1, 4, 5, 13, 3, 9, 11, 10, 2, 6])

    print("Total y: {}".format(box.height))
    for y in xrange(box.miny, box.maxy):
        if (y-box.miny)%5 == 0:
            print("y: {}".format(y-box.miny))
        for x in xrange(box.minx, box.maxx):
            for z in xrange(box.minz, box.maxz):
                # Gotta match the find block.
                if not matches(find_except, find_block, level, x, y, z):
                    continue

                # Get noise value.
                noise = perlin(x - box.minx, y - box.miny, z - box.minz)
                if noise <= proportion:
                    level.setBlockAt(x, y, z, block_id)
                    level.setBlockDataAt(x, y, z, block_data)

                # Test noise distribution. Uncomment this and the other line for
                # a cheeky visual of the "perlin" noise.
                # level.setBlockAt(x, y, z, 35)
                # level.setBlockDataAt(x, y, z, woolid[(int)(noise * 16)])


    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return
