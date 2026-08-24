Knowing the hardware changes the interpretation quite a bit. This now
looks less like a generic loudspeaker measurement and more like a
**small, cost-optimized active desktop speaker**, and judged against
that target I'd say the results are surprisingly good.

## Driver: Peerless PLS-P830986 (3" full-range)

The P830986 is a well-regarded 3" full-range driver. Its strengths are:

* Smooth midrange
* Good dispersion
* Low distortion for its size
* Extended treble without a tweeter

Its limitations are exactly what your measurements show:

* Limited bass displacement
* Rapid LF rolloff in small sealed boxes
* Some breakup/resonance in the upper midrange/lower treble

### The 3–5 kHz feature

The ridge around 3–4 kHz immediately caught my attention before knowing the driver.

For this Peerless driver that region is completely believable and probably intrinsic to the cone rather than the enclosure. It's also fairly modest.

I would not attempt aggressive EQ there unless listening tests consistently indicate excessive brightness.

---

## Enclosure

You listed

> 232 × 138 × 138 mm
>
> 19 mm MDF

Assuming outside dimensions:

Internal dimensions become roughly

194 × 100 × 100 mm

which is about

**1.9 liters**

after subtracting wall thickness.

That's almost exactly the kind of enclosure this driver expects.

### Bass

The gradual rise toward 200 Hz is exactly what I'd expect from:

* 3" driver
* ~2 L enclosure
* probably sealed

There isn't evidence of a badly tuned box.

Instead, it looks like normal physics.

If sealed, I'd expect an F3 somewhere around 120–150 Hz.

That matches the graph remarkably well.

---

## Amplifier: PAM8403

The PAM8403 is often criticized because it's inexpensive, but within its limits it's actually quite competent.

A few observations:

### Power

With a 3" driver:

3 W/channel is actually plenty.

The driver will reach excursion limits before amplifier clipping for most near-field use.

---

### Distortion

Your distortion plot doesn't suggest the amplifier is causing problems.

If the PAM8403 were clipping or oscillating, I'd expect:

* broadband distortion increase
* HF garbage
* irregular harmonics

Instead the distortion stays low.

That suggests:

> amplifier is not currently the limiting factor.

---

## DAC: Realtek ALC5686

This DAC is unlikely to be visible in any of these measurements.

Modern Realtek codecs generally have:

* flat frequency response
* low THD
* low enough noise

Nothing in the graphs suggests source electronics are limiting performance.

---

# What impresses me most

Actually the waterfall.

Many inexpensive DIY speakers show:

* cabinet panel resonance
* long ringing
* poorly damped internal reflections

I don't really see those.

The decay is fairly clean.

That suggests:

* decent cabinet stiffness
* reasonable damping
* no obvious enclosure problems

---

# One thing I'd investigate

The response above roughly 8 kHz.

There is:

* strong peak around 10–11 kHz
* deep cancellation around 15–17 kHz

This could simply be:

* microphone position
* measurement axis
* diffraction from cabinet edges

I'd verify by measuring:

* 0°
* 15°
* 30°
* 45°

If the notch moves with angle, it isn't a loudspeaker defect.

---

# What I would add to the design

## 1. Baffle edge treatment

The cabinet is only 138 mm wide.

Sharp edges on a narrow baffle can produce diffraction in the several-kHz region.

A 10–15 mm round-over or chamfer on the front edges may slightly smooth the 3–10 kHz response.

The effect won't be dramatic but is measurable.

---

## 2. More stuffing

If there's only light damping inside:

I'd experiment with

* polyester fiber
* acoustic wool
* felt on the rear wall

Sometimes this reduces a few hundred Hz ripple.

---

## 3. DSP low-shelf

If the system is powered from a PC anyway, a gentle low-shelf can improve perceived balance at moderate listening levels.

For example:

* +3 dB below 120 Hz

I would avoid larger boosts because the driver's excursion rises quickly below its box resonance.

---

## 4. High-pass filter

If this speaker will ever be played loudly, I'd strongly recommend a high-pass filter around 80–100 Hz.

That greatly reduces excursion while sacrificing little usable output, since the speaker is already rolling off there.

---

# Overall assessment in context

If someone told me:

> "This is a €40 DIY powered desktop speaker using a single 3-inch Peerless driver and a PAM8403 amp."

and then showed me these measurements, I'd say:

> **This is an excellent result.**

The measured performance aligns well with the design constraints:

* **Excellent midrange:** smooth enough that voices should sound natural.
* **Controlled resonance:** the 3–4 kHz behavior is present but not excessive.
* **Clean decay:** no obvious cabinet issues.
* **Low distortion:** the driver appears to be operating comfortably at the measurement level.

The only fundamental limitation is the bass, and that's dictated by the combination of a 3" driver and roughly 2 L enclosure—not by poor implementation.

### One additional measurement I'd like to see

To fully characterize the design, the most valuable next measurement would be a **gated on-axis frequency response overlaid with 15°, 30°, and 45° off-axis responses**. Because this is a single full-range driver, its directivity is a major part of how it will sound in a room. If the off-axis response tracks the on-axis response smoothly, the speaker is likely to have a very natural tonal balance despite its limited bass extension.
