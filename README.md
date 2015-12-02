# rpi0watch

Simple script which periodically checks if RaspberryPi Zero is back in stores 
and sends notification email if so.

## Requirements
- Python >= 3.4

## Configuration files example

### maillist.json

  ```
  [
    "some.email@gmail.com",
    "another.email@gmail.com",
    "yetanotheremail@yahoo.com"
  ]
  ```


### gmail.json

  ```
  {
    "login": "youremail@gmail.com",
    "pass": "app.password"
  }
  ```
