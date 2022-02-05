'''
The models for the application database.
'''
from app import db
from werkzeug.security import check_password_hash,generate_password_hash


class User( db.Model): 
    __tablename__ ='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    crop_coordinate = db.relationship("Crop_coordinate",back_populates="user")
    amplitude_experiment_parameter = db.relationship("Amplitude_experiment_parameter",back_populates="user")
    blob_detector_parameter = db.relationship("Blob_detector_parameter",back_populates="user")

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self,password):
      self.password_hash = generate_password_hash(password)
    def check_password(self, password):
      return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

class Crop_coordinate(db.Model): 
  __tablename__ ='crop_coordinate'
  id = db.Column(db.Integer, primary_key=True)
  name= db.Column(db.String(64), index=True, unique=True)
  left = db.Column(db.Float)
  right = db.Column(db.Float)
  top = db.Column(db.Float)
  bottom = db.Column(db.Float)
  # User 表的外键，指定外键的时候，是使用的是数据库表的名称，而不是类名
  user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
  # 在 ORM 层面绑定两者之间的关系，第一个参数是绑定的表的类名，
  # 第二个参数 back_populates 是通过 User 反向访问时的字段名称
  user = db.relationship('User',back_populates="crop_coordinate")

  def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

class Amplitude_experiment_parameter(db.Model):
  __tablename__ ='amplitude_experiment_parameter'
  id_= db.Column(db.Integer, primary_key=True)
  simulate = db.Column(db.Integer) # 1 = generated random images, 0 = get images over http
  id = db.Column(db.String(64), unique=True) # Identifier of the experiment run
  desired_particles = db.Column(db.Integer) # How many particles should be on the plate, at least, for the experiment to start
  desired_stepSize = db.Column(db.Integer) # The experiment tries to adjust the amplitudes so that the 75% of the particles move less than this
  cycles = db.Column(db.Integer) # For each frequency, how many PTV steps is taken in total. The total number of exps cycles * number of frequencies
  minfreq = db.Column(db.Float) # All notes from the scale below this frequency are discarded.
  maxfreq = db.Column(db.Float) # All notes from the scale above this frequency are discarded
  duration = db.Column(db.Float) # in milliseconds, constant for all notes
  default_amp = db.Column(db.Float) # starting amplitude: for 2*3*5 actuators = 0.02 for 2*3*20 actuators = 0.005
  min_amp = db.Column(db.Float) # never decrease amplitude below this
  max_amp = db.Column(db.Float) # never increase amplitude above this
  max_increase = db.Column(db.Float) # never increase the amplitude more than 1.5 x from the previous experiment
  exps_before_reset = db.Column(db.Integer) # The balls are replaced to good locations every this many cycles
  basescale = db.Column(db.PickleType) # C major
  # basescale = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88] # chromatic
  user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
  user = db.relationship('User',back_populates="amplitude_experiment_parameter")

  def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

class Blob_detector_parameter(db.Model): 
  __tablename__ ='blob_detector_parameter'
  id= db.Column(db.Integer, primary_key=True)
  minThreshold= db.Column(db.Float)
  maxThreshold= db.Column(db.Float)
  filterByColor= db.Column(db.Boolean)
  blobColor= db.Column(db.Float)
  filterByArea= db.Column(db.Boolean)
  minArea= db.Column(db.Float)
  maxArea= db.Column(db.Float)
  filterByCircularity= db.Column(db.Boolean)
  minCircularity= db.Column(db.Float)
  filterByConvexity= db.Column(db.Boolean)
  minConvexity= db.Column(db.Float)
  filterByInertia= db.Column(db.Boolean)
  minInertiaRatio= db.Column(db.Float)
  user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
  user = db.relationship('User',back_populates="blob_detector_parameter")

  def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

class Role(db.Model):
  __tablename__ = 'role'
  id= db.Column(db.Integer, primary_key=True)
  has_admin=db.Column(db.Boolean)
  user_id = db.Column(db.Integer)
  def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

