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
def iterate(level, box, method=BLOCKS):
    # fucking finally found the culprit of the chunk skipping bug. i believe the
    # chunks were being unloaded before the changes could be made/saved/
    # something. idk exactly why this was happening, but keeping a reference in
    # here of every chunk seems to have fixed it.... so should be good....
    chunks = []

    # Iterate through the level selection.
    for chunk, slices, point in level.getChunkSlices(box):
        # Keep this chunk loaded.
        chunks.append(chunk)

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
# which must be the same shape and dtype as `out`. `out` may be the same memory
# as `array`, which causes an inplace shift.
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



# Returns the slices that would index `slice(start, end, step)` along the given
# axis, and then every element along the others.
def slices(axis, start, end, step=None):
    return axis*(slice(None),) + (slice(start, end, step),)



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



# Returns the shape of the box, in x,z,y order.
def shape(box):
    # Cheeky unpack, reorder and repack.
    w, h, l = box.size
    return w, l, h


# Returns the slices of the box, in x,z,y order.
def box_slices(box):
    x, y, z = [slice(p1, p2) for p1, p2 in zip(box.origin, box.maximum)]
    return x, z, y



















# LMAO. i am leaving this here as a relic. you see, once upon a time i wished to
# improve upon the progress readout from br-filters 1. so i made a cool little
# progress bar, spent a couple (more) hours tryna perfect it, make it threaded,
# ya know. However. it is after completing the rework of the smooth filter that i
# stand here, high among the stars, and realise the world i left behind. you see,
# i did not realise my journey of filter improvement would lead me to such
# places. It has gotten to the point that every single filter has been sped up by
# such a degree that it can genuinely be considered instaneous (<0.1 seconds).
# And what does this mean for our measily little progress readout? Well, it's
# completely, entirely, utterly useless. Goodbye progress readout, you will be
# missed.



# Prints the progress of an iterable as a progress bar.
def __progress(title, iterable, total=None):
    if total is None:
        total = len(iterable)

    start = time.time()

    # Store the previous line length to fully wipe it.
    prev_len = 0

    # Only update the printer every so often to prevent needless printing. Use a
    # pow2-1 with logical & for speedy triggering once every few.
    check = prev_pow2(total // 100) - 1

    # Don't do something dumb.
    if check < 0:
        check = 0

    for i, item in enumerate(iterable):
        if not (i & check):
            # Get how done.
            how_done = float(i) / float(total)
            how_done = np.clip(how_done, 0.0, 1.0) # justin caseme.

            # Get the line to print, and update the previous line length.
            line, prev_len = get_line(title, start, how_done, prev_len)
            stdout.write(line)
            stdout.flush()

        yield item

    # We done so print hundy. Also chuck a newline in there.
    line, _ = get_line(title, start, 1.0, prev_len)
    stdout.write(line + "\n")
    stdout.flush()


    # ive tried threading this printing but its literally slower because of the
    # stoopid gil. dumbest thing i ever saw. anyway i also cant use multiprocess
    # because i think an issue with tkinter/mcedit/windows causes it to launch a
    # new mcedit window LITERALLY NO MATTER WHAT I DO. HOW DOES IT NOT REALISE
    # THAT MORE MCEDITS WILL NOT MCEDIT FASTER. anyway so here we are with this
    # single-threaded non-async chugging-along monstrosity. but the other thing
    # is that python is actually just ridiculously slow, and more than half the
    # slowdown of the printer is caused literally just from:
    # def func(iterable):
    #   for x in iterable: yeild x
    # so yeah no threading will speed that up.
    # but also it doenst make a measurable difference on intense filters which
    # actually benefit from it, so ya know kinda pointless anyway. but still
    # annoying af.



def __get_line(title, start, how_done, prev_len):
    # Total width of the progress bar.
    NUM_TICKS = 20

    # Store how much time its taken so far.
    taken = time.time() - start

    # Get the number of full ticks to display and do the actual progress bar.
    ticks = int(round(how_done * NUM_TICKS))
    bar = "=" * ticks + "-" * (NUM_TICKS - ticks)


    if how_done < 1.0:
        # Get the time estimate left. This is probably a really naive way to
        # do it, which is exactly why thats how im doing it.
        if how_done > 0.0:
            taketh = taken / how_done - taken
        else:
            # dont div by zero idot.
            taketh = 99.9

        # im gonna call him... timey (i cant spell).
        timey = "[~{:.1f}s left]".format(taketh)
    else:
        # If we done, jsut display how long it took.
        timey = "[took {:.1f}s]".format(taken)


    # Put the line together, wiping the previous line with '\r'.
    line = "\r{}: {} {}% {}".format(title, bar, int(100*how_done), timey)

    # Gotta ensure all characters from the previous line are overwritten, so
    # pad with spaces.
    this_len = len(line)
    line = line + " "*max(prev_len - this_len, 0)

    return line, this_len
