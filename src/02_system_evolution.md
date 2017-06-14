# Integrators: How the system evolves

In the previous section we have seen how a physical system is represented in Lumol:
* all the spatial information is located in the `Configuration`
* all the interactions between particles in `Interactions`

These two structures are actually contained in another one: the `System`.

```rust
pub struct System {
    configuration: Configuration,
    interactions: Interactions,
    kinds: BTreeMap<String, ParticleKind>,
    step: u64,
    external_temperature: Option<f64>,
}
```

* `kinds` is a way to map a particle name to its `ParticleKind` identifier
* `external_temperature` is exactly what it seems: a way to specify a temperature 
for the system due to an external factor
* `step` is what we are interested in for now: it starts at 0, and is incremented 
every time the system "evolves". What exactly it means to evolve is up to the `Integrator`
we use

## Integrators

There are 3 categories of integrators, corresponding to a type of simulation:
* **molecular dynamics**: the most intuitive one, we simulate how particle move given
the forces applied to them using the laws of physics. The system's `step` corresponds
to a time step
* **Monte Carlo simulation**: here the goal is to try to move particles in the system, and 
accepts these moves randomly (based on how likely these moves are to happen). The system's 
`step` corresponds to trying a move
* **energy minimization**: minimizes the energy of the system. The system's 
`step` corresponds to a step in the minimization algorithm

Integrators have a very simple API, defined by the `Integrator` trait:

```rust
pub trait Integrator {
    fn setup(&mut self, _: &System) {}
    fn integrate(&mut self, system: &mut System);
}
```

* `setup` is called once at the beginning of the simulation
* `integrate` is where the magic happens, it is called at each step and 
modifies the system

To get a little more concrete, let's look at the `Verlet` integrator. It 
computes the new positions of the particles using the following formula
(you can get the details of why this works on [Wikipedia][wiki-verlet]):

$$ 
x(t + \Delta t) = 2 x(t) - x(t - \Delta t) + a(t) \Delta t^2
$$

Where $x(t)$ is the position of a particle at time $t$, and $a(t)$ its
acceleration.

[wiki-verlet]: https://en.wikipedia.org/wiki/Verlet_integration

```rust
pub struct Verlet {
    /// Timestep for the integrator
    timestep: f64,
    /// Previous positions
    prevpos: Vec<Vector3D>,
}


impl Integrator for Verlet {
    fn setup(&mut self, system: &System) {
        self.prevpos = vec![Vector3D::zero(); system.size()];

        let dt = self.timestep;

        for (i, part) in system.particles().enumerate() {
            self.prevpos[i] = part.position - part.velocity * dt;
        }
    }

    fn integrate(&mut self, system: &mut System) {
        let dt = self.timestep;
        let dt2 = self.timestep * self.timestep;

        let forces = system.forces();
        for (i, part) in system.particles_mut().enumerate() {
            // Save positions at t
            let tmp = part.position;
            // Update positions at t + dt
            let position = 2.0 * tmp - self.prevpos[i] + dt2 / part.mass * forces[i];
            // Update velocities at t
            let velocity = (position - self.prevpos[i]) / (2.0 * dt);

            part.position = position;
            part.velocity = velocity;
            // Update saved position
            self.prevpos[i] = tmp;
        }
    }
}
```

The computation of $x(t + \Delta t)$ requires that we know $x(t - \Delta t)$: this 
makes the computation of the first step a little weird. This is why the first value
of $x(t - \Delta t)$ is approximated in the `setup`. The `integrate` method is 
a straight application of the formula (note that it also computes velocities).