import time
from pymclevel import alphaMaterials
import copy

displayName = "Block Coat"

inputs = (
    ("Find except?", False),
    ("Find:", alphaMaterials.Air),
    ("Replace except?", True),
    ("Replace:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("Depth:", (1, 1, 32767)),
    ("For every \"find\" block in the selection, searches the blocks around if that satisfy the \"replace\" block and replaces them with the \"block\" block, to a max depth of \"depth\".","label"),
)


def matches(is_except, block, level, x, y, z):
    level_block = (level.blockAt(x,y,z), level.blockDataAt(x,y,z))
    if is_except:
        return block != level_block
    else:
        return block == level_block



def perform(level, box, options):
    start = time.time()

    depth = options["Depth:"]

    block_id = options["Block:"].ID
    block_data = options["Block:"].blockData

    replace_except = options["Replace except?"]
    replace_block = (options["Replace:"].ID, options["Replace:"].blockData)

    find_except = options["Find except?"]
    find_block = (options["Find:"].ID, options["Find:"].blockData)

    # Need to cache every block to be placed until the entire search is done.
    # This is so that replacing the blocks mid operation doesn't lead to a
    # self-triggering endless cycle that will continue until the heat death of
    # the universe - just less than ideal really.

    # Do initial search to find the source blocks.
    seed = find_seed(level, box, find_except, find_block, replace_except, replace_block)


    # Now do the depth search with this as the seed.
    cache = coat_me(level, box, depth, seed, replace_except, replace_block)


    # Set all the blocks in the cache.
    for x,y,z in cache:
        level.setBlockAt(x, y, z, block_id)
        level.setBlockDataAt(x, y, z, block_data)

    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return


ADJ_MASK = tuple((x,y,z) for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1) if abs(x)+abs(y)+abs(z)==1)


def find_seed(level, box, find_except, find_block, replace_except, replace_block):
    seed = set()

    print("Initial pass.")
    print("Total y: {}".format(box.height))
    for y in xrange(box.height):
        if y%5 == 0:
            print("y: {}".format(y))
        y += box.miny
        for x in xrange(box.minx, box.maxx):
            for z in xrange(box.minz, box.maxz):
                # Its only purpose is to match the find block so probably should
                # do that.
                if not matches(find_except, find_block, level, x, y, z):
                    continue

                # Kinda optimisation here just to check that the source actually
                # has a replaceable block adjacent to it. It kinda just moves
                # where the work is but this one has the status readout soooo.
                add_it = False
                for coord in ((x+dx, y+dy, z+dz) for dx,dy,dz in ADJ_MASK):
                    # Gotta be in selection.
                    if coord not in box:
                        continue
                    # Gotta be replaceable.
                    if not matches(replace_except, replace_block, level, *coord):
                        continue
                    # Easy.
                    add_it = True
                    break

                # Add to the seed.
                if add_it:
                    seed.add((x,y,z))

    return seed


def coat_me(level, box, depth, seed, replace_except, replace_block):
    # Four caches:
    # - total: keeps it all.
    # - current: what was just found and what we finding the adjacents of.
    # - next: what we adding to rn.
    # Note this importantly means the all cache won't include the intial elements
    # of the current cache since thats the seed blocks not the replace blocks.
    cache = set()
    cur_cache = seed
    next_cache = set()

    print("Depth pass.")
    for i in range(depth):
        print("Depth: {}".format(i))

        # Add the adjacents of the current layer.
        for sx, sy, sz in cur_cache:
            # Check all adjacents.
            for coord in ((sx+dx, sy+dy, sz+dz) for dx,dy,dz in ADJ_MASK):
                # Gotta be in selection.
                if coord not in box:
                    continue
                # Can't have already been checked and can't be a seed block.
                if coord in cache or coord in seed:
                    continue
                # Gotta be replaceable.
                if not matches(replace_except, replace_block, level, *coord):
                    continue
                # Too easy.
                next_cache.add(coord)

        # Update caches.
        cache.update(next_cache)
        cur_cache = next_cache
        next_cache = set()

    # idk if returning is strictly necessary man fuck python mutability. gimme c
    # any day. id rather seg fault than be uncertain as to whether this return
    # is necessary or not.
    return cache
