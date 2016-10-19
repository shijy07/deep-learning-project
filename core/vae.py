import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import time
import os

 

class Variational_Autoencoder():
    def __init__(self, sess, build_encoder, build_decoder, checkpoint_name = 'vae_checkpoint',
    	batch_size = 100, z_dim = 20, img_dim = 784, dataset = 'mnist',
    	learning_rate = 0.001, num_epochs = 5,load = False,load_file = None,
        checkpoint_dir = '../notebook/checkpoints/'):
        """
        Inputs:
        sess: TensorFlow session.
        build_encoder: A function that lays down the computational
        graph for the encoder.
        build_decoder: A function that lays down the computational
        graph for the decoder.
        checkpoint_name: The name of the checkpoint file to be saved.
        batch_size: The number of samples in each batch.
        z_dim: the dimension of z.
        img_dim: the dimension of an image.
        (Currently, we only consider 28*28 = 784.)
        dataset: The filename of the dataset.
        (Currently we only consider mnist.)
        learning_rate: The learning rate of the Adam optimizer.
        num_epochs: The number of epochs.

        """
        self.sess = sess
        self.build_encoder = build_encoder
        self.build_decoder = build_decoder
        self.checkpoint_name = checkpoint_name
        self.z_dim = z_dim
        self.img_dim = img_dim
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.dataset = dataset
        self.num_epochs = num_epochs
        self.load = load
        self.load_file = load_file
        self.checkpoint_dir = checkpoint_dir
        # if dataset == 'mnist':
        #     # Load MNIST data in a format suited for tensorflow.
        #     self.mnist = input_data.read_data_sets('MNIST_data', one_hot=True)
        #     self.n_samples = self.mnist.train.num_examples
        if dataset == 'mnist' and load == False:
            # Load MNIST data in a format suited for tensorflow.
            self.mnist = input_data.read_data_sets('MNIST_data', one_hot=True)
            self.n_samples = self.mnist.train.num_examples
        if load:
            self.train()

    def train(self):
        """ Train VAE for a number of steps."""
        global_step = tf.Variable(0, trainable = False)


        # Compute the objective function.
        loss = self.build_vae()


        # Build a graph that trains the model with one batch of examples
        # and updates the model parameters.
        optimum = tf.train.AdamOptimizer(self.learning_rate).minimize(loss, global_step=global_step)

        # Build an initialization operation to run.
        init = tf.initialize_all_variables()
        self.sess.run(init)
        if self.load:
            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, self.load_file)
        else:
            num_batches = int(self.n_samples / self.batch_size)

            for epoch in xrange(self.num_epochs):

                avg_loss_value = 0.

                for b in xrange(num_batches):
                    # Get images from the mnist dataset.
                    batch_images = self.input()

                    # Sample a batch of eps from standard normal distribution.
                    batch_eps = np.random.randn(self.batch_size,self.z_dim)

                    # Run a step of adam optimization and loss computation.
                    start_time = time.time()
                    _, loss_value = self.sess.run([optimum,loss],
                                            feed_dict = {self.images: batch_images,
                                                        self.batch_eps: batch_eps})
                    duration = time.time() - start_time

                    #assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

                    avg_loss_value += loss_value / self.n_samples * self.batch_size

                # Later we'll add summary and log files to record training procedures.
                # For now, we will satisfy with naive printing.
                print 'Epoch {} loss: {}'.format(epoch + 1, avg_loss_value) 
            self.save(epoch)

    def save(self,epoch):
        self.saver = tf.train.Saver()
        self.saver.save(self.sess, os.path.join(self.checkpoint_dir, 
            self.checkpoint_name), global_step = epoch)

    def input(self):
        """
        This function reads in one batch of data.
        """
        if self.dataset == 'mnist':
            # Extract images and labels (currently useless) from the next batch.
            batch_images, _ = self.mnist.train.next_batch(self.batch_size)

            return batch_images

    def build_vae(self):
        """
        This function builds up VAE from encoder and decoder function
        in the global environment.
        """
        # Add a placeholder for one batch of images
        self.images = tf.placeholder(tf.float32,[self.batch_size,self.img_dim],
                                    name = 'images')

        # Create a placeholder for eps.
        self.batch_eps = tf.placeholder(tf.float32,[self.batch_size, self.z_dim], name = 'eps')
        # Construct the mean and the variance of q(z|x).
        self.encoder_mean, self.encoder_log_sigma2 = \
            self.build_encoder(self.images, self.z_dim)
        # Compute z from eps and z_mean, z_sigma2.
        self.batch_z = tf.add(self.encoder_mean, \
                        tf.mul(tf.sqrt(tf.exp(self.encoder_log_sigma2)), self.batch_eps))
        # Construct the mean of the Bernoulli distribution p(x|z).
        self.decoder_mean = self.build_decoder(self.batch_z,self.img_dim)
        # Compute the loss from decoder (empirically).
        decoder_loss = -tf.reduce_sum(self.images * tf.log(1e-10 + self.decoder_mean) \
                           + (1 - self.images) * tf.log(1e-10 + 1 - self.decoder_mean),
                           1)
        # Compute the loss from encoder (analytically).
        encoder_loss = -0.5 * tf.reduce_sum(1 + self.encoder_log_sigma2
                                           - tf.square(self.encoder_mean)
                                           - tf.exp(self.encoder_log_sigma2), 1)

        # Add up to the cost.
        self.cost = tf.reduce_mean(encoder_loss + decoder_loss)

        return self.cost

    def generate(self,num = 10,load = False,filename = None):
        """
        This function generates images from VAE.
        Input:
        num: The number of images we would like to generate from the VAE.
        """

        # At the current stage, we require the number of images to
        # be generated smaller than the batch size for convenience.
        assert num <= self.batch_size, \
        "We require the number of images to be generated smaller than the batch size."

        # Sample z from standard normals.
        sampled_z = np.random.randn(self.batch_size,self.z_dim)
        
        return self.sess.run(self.decoder_mean,\
                      feed_dict = {self.batch_z:sampled_z}) 

