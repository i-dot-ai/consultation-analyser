# TODO - this is pseudo-code to run the process.

# class ProcessConsultation:


#     def __init__(self, consultation_slug):
# 		self.consultation_slug = consultation_slug

#     def run(self):
#         if HostingEnvironment.isAWS() and not HostingEnvironment.isAWSbatch():
#             self.send_to_run_on_batch()
#         elif HostingEnvironent.isAWSbatch():
#              self.run_on_batch()
#         else:
#             self.process()

#     def send_to_run_on_batch():
#         send_to_batch(consultation_slug)
#         # Run my management command

#     def run_on_batch(self):
#          wake_up_sagemaker()
#          self.process()
#          # No need to close down - will be done by infra

#     def process(self):
#         assign_themes()
#         assign_labels()
