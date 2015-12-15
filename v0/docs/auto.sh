cp ../experiment.py .
cp -R ../widgets .
cp -R ../templates .

cp ../custom_widgets.py .
cp ../achan.py .
cp ../digital_channel.py .
cp ../interface.py .
cp ../packet_handler.py .
cp ../SPI_class.py .
cp ../I2C_class.py .
cp ../NRF24L01_class.py .
cp ../MCP4728_class.py .
cp ../NRF_NODE.py .
cp ../commands_proto.py .

cd Apps
rm -r *
cp -R ../../bin/* .
#for file in * ; do mv "$file" "${file}.py" ; done
cp ../__appinit__.py ./__init__.py
cd ..

cd experiments
rm -r *
cp -R ../../apps/* .
#for file in * ; do mv "$file" "${file}" ; done
#cp ../__appinit__.py ./__init__.py
cd ..



rm -rf docs
sphinx-apidoc -H "SEELablet" -A "Jithin B."  -F -o docs .
cp conf.py docs/conf.py
cp custom.css docs/_static/custom.css
cp manual.rst docs/manual.rst
cp interface.rst docs/interface.rst
cp videos.rst docs/videos.rst
cp introduction.rst docs/introduction.rst
cp experiments.rst docs/experiments.rst
cp Apps.rst docs/Apps.rst

cd docs

rm achan.rst
rm commands_proto.rst
rm conf.rst
rm custom_widgets.rst
rm digital_channel.rst
#rm experiment.rst
rm packet_handler.rst
rm template_exp.rst
rm widgets.* templates.*
rm MCP4728_class.rst

make html
#make latexpdf
cp -R ../js _build/html/
