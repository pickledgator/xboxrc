@0xea58bcac2fa96450;

using Cxx = import "/capnp/c++.capnp";
$Cxx.namespace("xboxrc");

struct Xbox @0x8000000000000050
{
	enum EventType {
		none @0;
		button @1;
		axis @2;
	}

	enum EventField {
		none @0;
		x @1;
		y @2;
		z @3;
		rx @4;
		ry @5;
		rz @6;
		hat0x @7;
		hat0y @8;
		a @9;
		b @10;
		tl @11;
		tr @12;
		select @13;
		start @14;
		mode @15;
		thumbl @16;
		thumbr @17;
		
	}

  timestamp		@0 : UInt64;
  type			@1 : EventType;
  field 		@2 : EventField;
  value 		@3 : Int32;
}
