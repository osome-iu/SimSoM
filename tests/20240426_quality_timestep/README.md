`model.py` is modified as follows: 

record the timestep at which simulation would end with (rho; epsilon) OUTSIDE while loops instead of INSIDE 

# TODO: move this block back inside the while loop — right now I'm testing
        # record the timestep at which simulation would end with (rho; epsilon)
        if self.quality_diff < self.epsilon:
            self.converged_rhoepsilon_timestep = self.time_step

        # Run simulation until convergence condition is met
        while eval(self.converge_condition):
            num_messages = sum([len(feed) for feed, _, _ in self.agent_feeds.values()])
            if self.verbose:
                self.logger.info(
                    f"- time_step = {self.time_step}, q = {np.round(self.quality, 6)}, diff = {np.round(self.quality_diff, 6)}, existing human/all messages: {self.num_human_messages}/{num_messages}, unique human messages: {self.num_human_messages_unique}, total created: {self.num_message_unique}"
                )
                self.logger.info("  exposure to harmful content: ", self.exposure)

            self.time_step += 1
            if self.tracktimestep is True:
                self.quality_timestep += [self.quality]
                self.exposure_timestep += [self.measure_exposure()]

            # Propagate messages
            self.simulation_step()

            self.update_quality()
