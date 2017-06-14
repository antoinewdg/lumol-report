---
title: Parallelization of the Lumol engine
author: Antoine Wendlinger
header-includes:
    - \usepackage{bbm}
    - \usepackage{graphicx,subcaption}
---


\newcommand{\isep}{\mathrel{{.}\,{.}}\nobreak}

# Lumol for the developer

Let's start by defining some terms:

* **particle**: in Lumol an atom
* **molecule**: set of particles, linked together
* **bond**: link between two particles of the same molecule
* **potential**: force applied to a molecule


The goal of this section is not to dive deep into the code of Lumol: it is to understand
how the core works on a more general level. However, looking how the data is organized 
in memory can help a great deal doing just this. This is why we start by reviewing the 
main structs used in Lumol.

## Main structs

### Particle

A particle is represented by the `Particle` struct:

```rust
pub struct Particle {
    name: String,
    pub kind: ParticleKind,
    pub mass: f64,
    pub charge: f64,
    pub position: Vector3D,
    pub velocity: Vector3D,
}
```

* `name` is the human-readable name of the particle (for example `H`, `C` or `O`)
* `kind` is an integer that has a one-to-one mapping to the `name` and is used to avoid having
to compare strings in the code (`ParticleKind` is an alias for `u32`, the Rust type for 32-bits 
unsigned integers)
* the other members are self-explanatory

Note that there is no mention of radius, shape or electrons, the effect of
these are simulated by [the interactions](#interactions)

### Configuration

The most important part of the Lumol engine is the `Configuration`: it contains every information about
the spatial configuration of the particles. The struct is defined as follows:

```rust
pub struct Configuration {
    pub cell: UnitCell,
    particles: Vec<Particle>,
    molecules: Vec<Molecule>,
    molids: Vec<usize>,
}
```

Most of the time, when making a simulation, we want to simulate only one small part of the system and 
repeat it indefinitely. This is particularly useful when simulating a liquid or a gas. The `cell` 
contains information about the shape and size of this small part of the system. `particles` 
is where most of the information is (see the definition of `Particle` above). All particles in 
the same molecule are store contiguously in memory. `molecules` contains the information about 
how particles are arranged into molecules (see the definition of `Molecule` below). `molids` maps 
a particle to the index of the molecule it belongs to.

### Molecule

A `Molecule` contains information about which particles are in this molecule, and how they are linked
together:

```rust
pub struct Molecule {
    bonds: HashSet<Bond>,
    angles: HashSet<Angle>,
    dihedrals: HashSet<Dihedral>,
    distances: Array2<BondDistance>,
    range: Range<usize>,
    cached_hash: u64
}
```

Since particles in the same molecule are contiguous in memory, a `Molecule` does not need to contain every
particle index, only the `range` of the indexes. `bonds`, `angles` and `dihedrals` are the three ways 
particles can be "linked" together inside a molecule, and each one is a set of the indices involved. 
**TODO: PUT LINK HERE**. 
**TODO: CACHED HASH ???**

### Example configuration

Here is what a `Configuration` would look like for a system with two H2O molecules:
![Example system configuration](../img/configuration.pdf)

### Interactions

The `Configuration` accounts for the spatial configuration of the physical system. Another
important piece of information is how all of these particles interact together. This is 
the role of the `Interaction` struct.

```rust
pub struct Interactions {
    pairs: BTreeMap<PairKind, Vec<PairInteraction>>,
    bonds: BTreeMap<BondKind, Vec<Box<BondPotential>>>,
    angles: BTreeMap<AngleKind, Vec<Box<AnglePotential>>>,
    dihedrals: BTreeMap<DihedralKind, Vec<Box<DihedralPotential>>>,
    pub coulomb: Option<Box<CoulombicPotential>>,
    pub globals: Vec<Box<GlobalPotential>>,
}
```

Let us not worry about the exact types used here and focus on how they are used. `PairKind` is simple a
2-tuple of `ParticleKind`. For example, a `PairKind` could correspond to a (C, O) couple. A `BondKind` is 
the same, an `AngleKind` is the same for 3 particles and `DihedralKind` for 4 particles. Note that these
types are different from the ones used in `Molecule` (such as `Bond`): the first refer to particle kinds,
while the latter refers to individual particles in the system.

* `pairs` maps a `PairKind` to a list of interactions that two molecules of these kinds can have when
they are **not** in the same molecule,
* `bonds` does the same for two particles in **the same** molecule,
* `angles` and `dihedrals` are similar to `bonds` but for 3 and 4 molecules,
* `coulomb` specifies the way electrostatic interactions are computed between charged particles (if they
are, if a system contains no charged particle this can be ignored)
* `globals` is a list are potentials that are applied to every particle individually

All of these potentials are specified by the user in an input file.



