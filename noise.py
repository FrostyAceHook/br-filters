import br
import numpy as np
from pymclevel import alphaMaterials

displayName = "Noise"

inputs = (
    ("Replace except?", True),
    ("Replace:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("Scale:", (6, 1, 256)),
    ("Octaves:", (2, 1, 20)),
    ("Proportion:", (0.4, 0.0, 1.0)),
    ("Scale controls the general size of the fluctations, octaves increase the chaos, proportion is roughly the percentage of blocks replaced.", "label"),
    ("Visualise:", False),
    ("just a cool option that replaces the entire selection with wool based on the noise generated from \"scale\" and \"octaves\" (red = 0.0, purple = 1.0).", "label"),
)


# Stuartian noise algorithm:
# Generate uniform random "nodes" spaced `scale` apart and then just linearly
# interpolate between them. Some distribution tweaking is performed at the end to
# make the distrubiton less centre-focussed. This may not be the most advanced
# noise algorithm, but it works just fine for these purposes and it is easy to
# implement in numpy, which is pretty much necessary to make it execute in <0.1s.
# Oh but uh, why not just use perlin?
# i din wanna


def perform(level, box, options):

    # Get those options.
    scale = options["Scale:"]
    octaves = options["Octaves:"]
    proportion = options["Proportion:"]
    visualise = options["Visualise:"]

    print "Scale: {}".format(scale)
    print "Octaves: {}".format(octaves)
    if not visualise:
        print "Proportion: {}".format(proportion)
    else:
        print "Acsending (visualising)"

    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    replace = br.from_options(options, "Replace")

    # LETS MAAAAAKE SOOOME NOOOOOOOOOISE
    noise = stuartian_noise(br.shape(box), scale, octaves)


    if not visualise:
        # Place on the blocks where the noise is less than the proportion,
        # effectively placing about `proportion` blocks.
        mask = (noise <= proportion)
        for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
            # Line up the matches and the mask.
            cur_mask = (replace.matches(ids, datas) & mask[slices])

            # Knock em down.
            ids[cur_mask] = bid
            datas[cur_mask] = bdata

    else:
        # Time to acsend.
        # red - purple, black for outlier. (hopefully doesn't happen lmao)
        rainbow = np.array([14, 1, 4, 5, 3, 9, 11, 10, 15])

        # Convert from the floating value to a value from 0 to len-1.
        noise *= len(rainbow) - 1
        wools = noise.astype(np.uint8)

        # Convert from the indices to the wool data values.
        for i in range(len(rainbow)):
            wools[wools == i] = rainbow[i] + 16
        wools -= 16

        # Taste the rainbow bitch.
        for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
            ids[:] = 35 # wool id.
            datas[:] = wools[slices]


    level.markDirtyBox(box)
    print "Finished making some noise."
    return



def stuartian_noise(shape, scale, octaves):
    # Create the noise in a slightly larger region than the selection to avoid
    # annoying issues with nodes being outside the region but obv still need to
    # access them. It will be cut down before returning. Note that the nodes
    # occur every `scale` blocks, that is there are `scale-1` blocks between
    # them.
    noise = np.random.random(map(lambda x: (x-2)/scale + 2, shape))
    # this numpy verion dunt got the new random generator.


    # If every block is a node, there is no need to do anything. The `correct`
    # function would leave data with scale=1 unchanged anyway so nothing is lost
    # by doing this. Also when scale=1 there is no excess space.
    if scale == 1:
        return noise


    # Do the linear interpolation along each axis. This is where the meat of the
    # smooth is. The lerp automatically fills in `scale-1` blocks between each
    # successive element, so this pads the selection to roughly the size of the
    # box, just slightly extended to incude the next node along.
    for axis in br.AXES:
        noise = lerp(noise, axis, scale)


    # Trim the noise back to the shape of the box.
    noise = noise[map(slice, shape)]


    # Add the octaves by recursing with a smaller scale. Don't do this if the
    # scale is already at a minimum.
    if octaves > 1:
        # Impact value is arbitrary. Is roughly controls how impactful the next
        # octave is to the noise. 0.6 seems pretty good at causing some chaos
        # without being all-consuming.
        impact = 0.6
        octave_scale = int((1.0 - impact) * scale)

        # Only keep going if the scale is at least 1.
        if octave_scale > 0:
            noise += impact * stuartian_noise(shape, octave_scale, octaves - 1)
            # Scale back to [0,1].
            noise /= (1 + impact)


    # Correct the values of the noise, which shifts the distribution such that
    # it's roughly a uniform distribution. Currently, it's very centre-focussed
    # so this just spreads it towards the edges of 0 and 1.
    noise = correct(noise, scale)


    # justin caseme.
    return np.clip(noise, 0.0, 1.0)



def lerp(data, axis, scale):
    # Note: don't go here w scale=1.

    # Algorithm: repeat the data along the array in the positive direction until
    # the node, multiply that all by some weight array which scales it correctly.
    # Repeat for the negative direction and sum.

    # Simple count down from [1, 0) in `scale` number of steps.
    weights = np.arange(scale, 0, -1, dtype=float)
    weights /= scale

    # Pad the dimensions of weights and set it up along the correct axis.
    pad_dims = (None,)*axis + (slice(None),) + (None,)*(data.ndim - axis - 1)
    weights = weights[pad_dims]


    # Get the repeated data and weights for the positive "iteration".
    repeated_pos = np.repeat(data, scale, axis=axis)
    weighted_pos = np.tile(weights, data.shape)

    # Now for the negative, take selective slices as if we'd repeated the data
    # and weights in the negative direction. This is possible because `repeated`
    # and `weighted` are too long by `scale-1` along the axis since they repeat
    # the last element when it's in fact the end.
    slice_from = br.slices(axis, scale - 1, None)
    slice_until = br.slices(axis, None, 1 - scale)

    repeated_neg = repeated_pos[slice_from]
    weighted_neg = 1 - weighted_pos[slice_until]
    # To avoid double-counting at nodes, just set each node weight to 0.
    weighted_neg[br.slices(axis, None, None, scale)] = 0.0


    # Do positive direction, cutting down to the correct size.
    lerped = weighted_pos[slice_until] * repeated_pos[slice_until]

    # Do negative direction. This doesn't need any cutting just because of how
    # it's setup.
    lerped += weighted_neg * repeated_neg

    return lerped



def correct(noise, scale):
    # Visualisation of the distribution inversion:
    # https://www.desmos.com/calculator/z5oj1dha65

    spread = lambda x: x*x*(3 - 2*x)
    s = spread(spread(noise))


    # The correction needed actually depends on the scale, smaller scales just
    # naturally have a more uniform distribution since a greater proportion of
    # the noise is literally a uniform distribution (the nodes). So, mix in a bit
    # of the uncorrected noise to essentially reduce the smoothness of the smooth
    # function.
    return (noise + (scale**2.2 - 1) * s) / scale**2.2


    # bunch of really rough scribbling/working if u wanna cop a geez.
    # https://www.desmos.com/calculator/yk9j6orqpg
