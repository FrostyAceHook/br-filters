import time
import numpy as np
from pymclevel import TileEntity, Entity


BLOCKS = 0 # Iterate through the blocks.
SLICES = 1 # Iterate through the blocks and slices of the selection.
CHUNKS = 2 # Iterate through the chunks.
TES = 3 # Iterate through the tile entities.
ENTITIES = 4 # Iterate through the entities.

# Iterates through the selection of the level. The `method` argument determines
# the format of the yielded values. The yielded values are as follows:
# - BLOCKS: `ids` and `datas` in the selection, in x,z,y order.
# - SLICES: `ids` and `datas`, as well as a `slices` mask which represents the
#           current section of the overall selection, all in x,z,y order.
# - CHUNKS: every `chunk` in selection.
# - TES: every tile entity in selection, as the tile entity id (`eid`), position
#        in x,y,z order (`pos`), and the compound itself (`te`).
# - ENTITIES: every entity in selection, as the entity id (`eid`), position in
#        x,y,z order (`pos`), and the compound itself (`entity`).
def iterate(level, box, method=BLOCKS, holey=False):
    # fucking finally found the culprit of the chunk skipping bug. i believe the
    # chunks were being unloaded before the changes could be made/saved/
    # something. idk exactly why this was happening, but keeping a reference in
    # here of every chunk seems to have fixed it.... so should be good....
    chunks = []

    # NEVERMIND IT STILL HAPPENS.
    # ok how about dirty every chunk immediately, AND keep a reference... surely
    # they cant get unloaded then?? or maybe that isn't even the culprit... it
    # does happen waaay less though now (after the previous change, haven't
    # tested this one yet, but that seems to indicate that the problem is at
    # least related to unloading).
    for chunk, slices, point in level.getChunkSlices(box):
        chunk.dirty = True
        chunks.append(chunk)


    # The `getChunkSlices` method will silently skip any chunks that don't exist,
    # but a lot of filters rely on the entire selection existing and being
    # iterated since blocks can influence other blocks. So we need to check that
    # the chunks do actually all exist. This isn't needed for all filters tho,
    # filters which only process entities have no need and filters explicitly
    # marked "holey" will be fine with missing chunks.
    if not (method in {TES, ENTITIES} or holey):
        for cx, cz in box.chunkPositions:
            if not level.containsChunk(cx, cz):
                raise Exception("Selection cannot contain missing chunks.")


    # Iterate through the level selection.
    for chunk, slices, point in level.getChunkSlices(box):
        # If the method is chunks, just yield the chunk.
        if method == CHUNKS:
            yield chunk
            continue

        # Entities and tile entites have a very similar api.
        if method == TES or method == ENTITIES:
            # Get the correct list of entities and their class.
            entities = chunk.TileEntities if (method == TES) else chunk.Entities
            entity_class = TileEntity if (method == TES) else Entity

            for entity in entities:
                # TileEntity and Entity have a position class method.
                pos = tuple(entity_class.pos(entity))

                # Still gotta bounds check.
                if pos not in box:
                    continue
                eid = entity["id"].value
                yield eid, pos, entity
            continue


        # The other methods all return the ids and datas.
        ids = chunk.Blocks[slices]
        datas = chunk.Data[slices]

        if method == BLOCKS:
            yield ids, datas
            continue

        # Get the properties of the current slice.
        pos = [point[i] for i in (0,2,1)]
        size = [s.stop - s.start for s in slices]

        # Make into slices for the overall selection.
        sel_slices = tuple(slice(p, p + s) for p, s in zip(pos, size))
        yield ids, datas, sel_slices
        continue




AXIS_X = 0 # Typically x-axis.
AXIS_Z = 1 # Typically z-axis.
AXIS_Y = 2 # Typically y-axis.
AXES = (AXIS_X, AXIS_Z, AXIS_Y) # All typical axes.

# Shifts the values of an array along an axis. Fills any now-empty values with 0
# if not clamping, otherwise fills it with the first perpendicular slice of the
# array along the shifted axis. `out` allows preallocated memory to be used,
# which must be the same shape and dtype as `array`. `out` may be the same
# memory as `array`, which causes an inplace shift.
def shift(array, by, axis, clamp=False, out=None):
    # No need - butch "Butch" Butch.
    if by == 0:
        if out is None:
            return np.copy(array)
        # Inplace shift of 0 is just nothing init.
        if out is array:
            return array

        # Otherwise use the memory provided.
        out[:] = array
        return out

    axis_len = array.shape[axis]

    # Create the array, if needed, which will be filled with the shifted `array`.
    if out is None:
        out = np.empty_like(array)


    # Slices the offset section of the shifted array to copy data to.
    shifted = slices(axis, abs(by), None)

    # Slices the section of the array to copy.
    unshifted = slices(axis, None, axis_len - abs(by))

    # If it's shifting backwards, just swap the slices.
    if by < 0:
        shifted, unshifted = unshifted, shifted


    # Do the shifted copy.
    out[shifted] = array[unshifted]


    # Now deal with the empty data.


    # Slices the empty part of the shifted array.
    empty = slices(axis, *((None, by) if (by > 0) else (by, None)))

    # If it's clamped gotta copy the data into the now empties.
    if clamp:
        # Slices the first non-empty slice of the shifted array, which is the
        # first slice of the original array. Do it like this so that `mem` can
        # actually be the same memory as array, if the original array is no
        # longer needed.
        clamped = slices(axis, *((by, by + 1) if (by > 0) else (by - 1, by)))

        # Fill the empty part.
        out[empty] = out[clamped]

    # Otherwise just zero fill.
    else:
        out[empty] = 0

    return out


# Same as `shift` however instead of only shifting along a single axis, shifts
# along all three axes by their respective `<axis>_by` slots.
def shift_xyz(array, x_by, y_by, z_by, clamp=False, out=None):
    if out is None and (x_by or y_by or z_by):
        out = np.copy(array)

    shift(array, x_by, AXIS_X, clamp=clamp, out=out)
    shift(out, y_by, AXIS_Y, clamp=clamp, out=out)
    shift(out, z_by, AXIS_Z, clamp=clamp, out=out)
    return out



# Returns the slices that would index `slice(start, end, step)` along the given
# axis, and then every element along the others.
def slices(axis, start, end, step=None):
    return axis*(slice(None),) + (slice(start, end, step),)


# Returns the shape of the box, in x,z,y order.
def shape(box):
    # Cheeky unpack, reorder and repack.
    w, h, l = box.size
    return w, l, h


# Returns the slices of the box, in x,z,y order.
def box_slices(box):
    x, y, z = [slice(p1, p2) for p1, p2 in zip(box.origin, box.maximum)]
    return x, z, y



# Stores a list of blocks, for finding/replacing/placing.
class Blocks:
    def __init__(self, ids, datas, is_except):
        if len(ids) != len(datas):
            raise Exception("Mismatched length of ids and datas.")

        self.ids = ids
        self.datas = datas
        self.count = len(ids)
        self.is_except = is_except


    # Iterate through each block id/data pair.
    def __iter__(self):
        return zip(self.ids, self.datas).__iter__()


    # Returns a boolean array that can be used to index `ids` or `datas` to find
    # elements which match according to this block list.
    def matches(self, ids, datas):
        # Initialise the indexing array. Initialise with 1 for use with & if
        # except, or 0 for use with | if not.
        if self.is_except:
            mask = np.ones(ids.shape, dtype=bool)
        else:
            mask = np.zeros(ids.shape, dtype=bool)

        # Now do the matching with the blocks.
        if self.is_except:
            for bid, bdata in self:
                # Find any coords where the id or data doesn't match and combine
                # with the previous matches to whittle down the selection.
                mask &= ((ids != bid) | (datas != bdata))
        else:
            for bid, bdata in self:
                # Find any coords where both id and data match and add to
                # previous selection.
                mask |= ((ids == bid) & (datas == bdata))

        return mask



# Initialises the block list from the options. Assumes the blocks exist as
# options in the form:
# - "{prefix} except?" (optional)
#
# - "{prefix}:"
# - "{prefix}?" (optional)
# OR
# - "{prefix} 1:"
# - "{prefix} 1?" (optional)
# - ...
# - "{prefix} {count}:"
# - "{prefix} {count}?" (optional)
def from_options(options, prefix, count=1):
    # Get if its an inverted selection.
    is_except = False
    except_opt = "{} except?".format(prefix)
    if except_opt in options:
        is_except = options[except_opt]

    # Get the blocks.
    ids = []
    datas = []
    for i in range(1, count + 1):
        # If there's only one block, it's not numbered.
        if count == 1:
            block_opt = "{}".format(prefix)
        # Otherwise add the number.
        else:
            block_opt = "{} {}".format(prefix, i)

        # Get if it optional.
        optional_opt = "{}?".format(block_opt)
        if optional_opt in options: # so many options
            if not options[optional_opt]:
                continue

        # Get the block.
        block = options["{}:".format(block_opt)]
        ids.append(block.ID)
        datas.append(block.blockData)

    return Blocks(ids, datas, is_except)
